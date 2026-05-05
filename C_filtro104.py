import os, io, logging, telebot, html, time, random, threading
from PIL import Image
from telebot import types
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from google.genai import types as genai_types
from C_shared100 import GeminiClient, CaptionGenerator, HealthServer, is_allowed

# --- VERSIONE ---
VERSION = "1.0.4"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN        = os.environ.get("TELEGRAM_TOKEN_FX")
MODEL_ID     = "gemini-3-pro-image-preview"
MODEL_TEXT_ID = "gemini-3-flash-preview"

gemini  = GeminiClient()
caption = CaptionGenerator(gemini)
server  = HealthServer("Filtro", VERSION)

# --- STATO UTENTE ---
user_filter   = defaultdict(lambda: None)   # filtro selezionato
user_category = defaultdict(lambda: None)   # categoria selezionata
pending       = {}                          # {uid: {'img': bytes, 'filter_key': str}}
last_img      = {}                          # {uid: bytes} — ultima immagine usata
last_prompt   = {}                          # {uid: str} — ultimo prompt inviato all'API

executor = ThreadPoolExecutor(max_workers=4)

# --- STATO RACCOLTA MOSAIC ---
mosaic_collecting = {}   # {uid: {'photos': [bytes,...], 'timer': Timer}}

# --- CARICAMENTO MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("masterface.png"):
            with open("masterface.png", "rb") as f:
                data = f.read()
            logger.info("✅ masterface.png caricata correttamente.")
            return genai_types.Part.from_bytes(data=data, mime_type="image/png")
        logger.warning("⚠️ masterface.png non trovata.")
        return None
    except Exception as e:
        logger.error(f"❌ Errore caricamento master_face: {e}")
        return None

MASTER_PART = get_face_part()

# --- STILI ARTISTICI (per filtro artistic_style) ---
ARTISTIC_STYLES_POOL = [
    "🌂 Magritte — surrealist hyper-realism, dreamlike impossible juxtapositions, Belgian surrealism",
    "🌀 Dalì — melting surrealist dreamscape, hyper-detailed hallucination, elongated figures, Spanish surrealism",
    "🏛️ De Chirico — metaphysical painting, long dramatic shadows, empty piazzas, classical architecture, eerie stillness",
    "🔷 Mondrian — primary color geometric grid, De Stijl abstraction, flat bold rectangles",
    "🖌️ Banksy — urban stencil street art, black and white spray paint, sharp political irony, graffiti aesthetic",
]

ARTISTIC_STYLE_PROMPTS = {
    "🌂 Magritte": (
        "Reinterpret the uploaded image in the style of René Magritte. "
        "Preserve the subject's identity and general composition but apply surrealist hyper-realism: "
        "dreamlike impossible juxtapositions, objects out of context, Belgian surrealism aesthetic. "
        "Palette: cool grey, ivory, soft pastel tones. Solid colors only, no patterns. "
        "Background: seamless white studio or minimal dreamlike setting. "
        "Maintain photographic quality with a painted surrealist atmosphere."
    ),
    "🌀 Dalì": (
        "Reinterpret the uploaded image in the style of Salvador Dalì. "
        "Preserve the subject's identity but apply melting surrealist dreamscape: "
        "hyper-detailed hallucination, elongated surreal elements, Spanish surrealism. "
        "Palette: earthy terracotta, ochre, warm amber. Solid colors only, no patterns. "
        "Background: desert at golden hour or vast dreamlike landscape. "
        "Ultra-detailed with a painted surrealist atmosphere."
    ),
    "🏛️ De Chirico": (
        "Reinterpret the uploaded image in the style of Giorgio De Chirico. "
        "Preserve the subject's identity but apply metaphysical painting aesthetics: "
        "long dramatic shadows, eerie stillness, classical architecture elements, empty piazzas. "
        "Palette: earthy terracotta, warm ivory, cool grey. Solid colors only, no patterns. "
        "Background: ancient ruins or empty classical piazza with dramatic shadows. "
        "Wide angle full body composition preferred."
    ),
    "🔷 Mondrian": (
        "Reinterpret the uploaded image in the style of Piet Mondrian and De Stijl. "
        "Preserve the subject's general silhouette but transform the aesthetic with: "
        "primary color geometric grid, flat bold rectangles of red, blue, yellow, black and white. "
        "Solid colors only, no patterns. Background: white seamless or geometric grid. "
        "Flat 2D graphic quality with bold black outlines separating color blocks."
    ),
    "🖌️ Banksy": (
        "Reinterpret the uploaded image in the style of Banksy street art. "
        "Transform into urban stencil art: black and white spray paint aesthetic, "
        "sharp political/artistic irony, graffiti on a brick wall or urban surface. "
        "Palette: monochromatic black and white with a single bold red accent element. "
        "Solid colors only. Background: urban brick wall, street setting. "
        "Stencil spray paint texture, rough edges, authentic street art feel."
    ),
}

def build_artistic_style_prompt():
    """Estrae uno stile casuale e costruisce il prompt per il filtro."""
    import random
    style = random.choice(ARTISTIC_STYLES_POOL)
    # Trova la chiave giusta (emoji + nome artista)
    key = next((k for k in ARTISTIC_STYLE_PROMPTS if k in style), None)
    if key:
        return ARTISTIC_STYLE_PROMPTS[key], style
    return ARTISTIC_STYLE_PROMPTS["🌂 Magritte"], style

# ============================================================
# FILTRI
# ============================================================

FILTERS = {

    # ── STILISTICI ──────────────────────────────────────────
    "cinematic_highangle": {
        "label": "⬆️⬇️ Cinematic High-Angle",
        "cat": "stylistic",
        "prompt": (
            "Apply a photographic filter. "
            "A cinematic high-angle portrait, looking up at the camera, intense expressive eyes with sharp focus. "
            "Shot from an overhead perspective creating depth and vulnerability, shallow depth of field with softly blurred concrete background, "
            "dramatic soft lighting with subtle shadows, moody color grading, high contrast, ultra-realistic skin tones, "
            "professional fashion photography style, 85mm lens look, f/1.8, cinematic realism, editorial portrait, "
            "8K detail, film grain, modern aesthetic, photorealistic."
        )
    },
    "dramatic": {
        "label": "⬆️ Dramatic Low-Angle",
        "cat": "stylistic",
        "prompt": (
            "Apply a photographic filter with an extreme low-to-high angle, sharply focusing on the foreground. "
            "Dramatically increase contrast and saturation, making colors rich and deep, especially reds and blacks, "
            "while heavily darkening the background to create a dramatic, theatrical effect with bright, direct lighting."
        )
    },
    "glossy": {
        "label": "🌟 Glossy Opal",
        "cat": "stylistic",
        "prompt": (
            "Apply the 'Ultra-Opal Fairy-Angel Couture V2' style: hyper-glamour rendering with 3D iridescent aesthetics, "
            "multi-layered pearlescent reflections, rainbow opalescence and liquid glows reminiscent of fairy wings, "
            "Swarovski crystals and mirror-gloss surfaces. Lighting is extra-luxury: soft, enveloping, with golden-pink "
            "atmospheric scattering, suspended micro-sparkles, clean flares and precious bokeh producing pearlescent bubble spheres. "
            "Every surface is ultra-detailed: ultra-fine glitter, multicolor refractions, wet and metallic highlights, "
            "superior material depth, 'angel couture runway' effect. Only the outfit receives iridescent shifting reflections "
            "with pearl-champagne tone and cold-pink hot spots with blue-opal touches. No effects on skin."
        )
    },
    "iridescent": {
        "label": "🌈 Iridescent",
        "cat": "stylistic",
        "prompt": (
            "Rendered with an extreme iridescent and opalescent finish. The lighting must use dichroic refraction to create "
            "a spectrum of shifting colors between electric teal, deep cosmic blue, and fiery metallic orange. "
            "Surfaces (NOT THE SKIN, ANYWHERE) should have a pearlescent glow with high-gloss textures and micro-crystalline details. "
            "Incorporate prismatic light dispersion and volumetric studio lighting to emphasize sharp edges and intricate decorations. "
            "The color palette is dominated by a high-contrast complementary scheme of burning gold and vibrant cyan. "
            "Every highlight should shimmer with a holographic effect, mimicking the interplay of light on diamonds and silk flowers. "
            "Ultra-high definition, 8K, cinematic fashion aesthetic."
        )
    },
    "galaxy": {
        "label": "🌌 Galaxy Couture",
        "cat": "stylistic",
        "prompt": (
            "Apply an exclusive 'jewel galaxy haute couture' aesthetic filter to the uploaded image. "
            "Keep the subject, composition and base shapes of all elements in the photo unchanged; do not add or remove "
            "recognizable elements, limiting modifications to color, texture and lighting. "
            "Reconfigure the palette to midnight blue, purple, turquoise and warm gold, with soft iridescent tones reminiscent "
            "of nebulae and cosmic skies. Add brilliant metallic reflections and colored edge glints to objects, as if coated "
            "in iridescent metal. Introduce small gem and crystal-like lights in amber-orange, aquamarine and opalescent white "
            "tones, only as decorative details on existing surfaces. Enhance contrast and sharpness for extremely detailed textures, "
            "with soft studio lighting emphasizing reflections. Hyper-realistic, fashion cover look, no additional text in image. "
            "Apply the filter only to colors and textures; do not modify object shapes."
        )
    },

    "arabesque": {
        "label": "🌹 Arabesque",
        "cat": "stylistic",
        "prompt": (
            "Transform this image into an explosion of supreme opulence and baroque maximalism. "
            "Every surface must be smothered in ornament — no bare space permitted anywhere. "
            "Layer upon layer of: intricate gold filigree crawling across every edge, "
            "Sicilian baroque architectural motifs (acanthus scrolls, cartouches, broken pediments), "
            "Dolce & Gabbana-style sacred imagery fused with high fashion (Byzantine gold mosaics, "
            "maiolica tile patterns in cobalt and gold, Trinacria symbols, Norman-Arab geometric lattices), "
            "Versailles excess (gilded mirrors, brocade drapery, crystal chandeliers multiplied into infinity), "
            "Venetian carnival richness (damask silks, Murano glass jewels, hand-painted fan motifs), "
            "Terry Gilliam-style compositional chaos — elements piled on elements with theatrical intentionality, "
            "cherubs and putti erupting from corners, garlands of roses and pomegranates cascading downward, "
            "tapestry-like backgrounds with interlocking arabesques and Iznik floral patterns in crimson, "
            "cobalt, emerald and gold. "
            "The subject's outfit must be transformed into the most encrusted, jewel-laden, embroidered, "
            "beaded and gold-threaded garment imaginable — every centimeter covered in decoration. "
            "Skin and face remain photorealistic and untouched. "
            "Color palette: deep crimson, imperial gold, byzantine cobalt, emerald green, ivory and black. "
            "The overall effect must feel simultaneously overwhelming, magnificent, and intentional — "
            "baroque maximalism as high art, not kitsch. Ultra-detailed 8K, cinematic lighting with "
            "dramatic chiaroscuro emphasizing the sculptural depth of every ornamental layer."
        )
    },
    # ── FANTASY & ART ────────────────────────────────────────
    "stained_glass": {
        "label": "🎐 Stained Glass",
        "cat": "fantasy",
        "prompt": (
            "Apply this filter to the image: a hyper-realistic subject made entirely of stained glass and translucent crystal. "
            "The whole body is a mosaic of milky white and pale blue glass tiles, held together by an intricate polished silver wire frame. "
            "Ethereal glowing aquamarine eyes with crystalline details. The hair flows in sculpted waves of transparent teal glass. "
            "Soft cinematic lighting hitting the metallic edges, creating brilliant specular highlights and internal refractions. "
            "Elegant, sculptural, avant-garde art style. Dark moody background, 8K resolution, shot on 85mm lens, "
            "macro photography detail, iridescent textures."
        )
    },
    "underwater": {
        "label": "🧜 Underwater Gold",
        "cat": "fantasy",
        "prompt": (
            "High-fantasy underwater style with high-brilliance gold and saturated turquoise/teal palette, "
            "volumetric lighting from above, translucent flowing fabrics like silk, hyper-detailed jewelry in gold "
            "and turquoise stones, thousands of micro-bubbles and suspended particles, mystical atmosphere in deep "
            "blue-cyan water, ultra-detailed glossy high-contrast rendering with specular reflections."
        )
    },
    "3d_synthetic": {
        "label": "🪟 3D Synthetic",
        "cat": "fantasy",
        "prompt": (
            "Generate a hyper-realistic cutting-edge 3D rendering of the provided image. Transform the subject's material "
            "into a high-quality translucent synthetic material with a dazzling glossy multichromatic finish. Its surface "
            "should feature a subtle knurled texture, precision-engineered to refract light into razor-sharp specular reflections. "
            "The scene is illuminated with a powerful multi-source HDRI studio setup, characterized by intense rim lighting "
            "and backlighting sculpting the form. The dominant color combination is a sophisticated blend of electric cyan, "
            "deep violet and hints of molten gold, creating an energetic yet refined gradient on the material. "
            "Implement pronounced bloom effects, subtle chromatic aberration and a delicate bloom effect to enhance the futuristic aesthetic. "
            "Absolute black background will amplify the subject's radiant luminosity. The camera captures a flat, frontal, "
            "eye-level perspective using a macro lens that subtly warps light at the edges. Ensure the foreground is in sharp focus, "
            "no depth of field effects. Final touches: aggressive contrast enhancement, saturated spectrum color grading "
            "and an almost imperceptible layer of digital grain."
        )
    },
    "graffiti": {
        "label": "🧯 Graffiti Artist",
        "cat": "fantasy",
        "prompt": (
            "Create one ultra-realistic image showing the same person as the reference spray-painting a full-body "
            "self-portrait graffiti on an urban brick wall. The person is standing or half-crouched, mid-spray, "
            "while the entire head-to-toe mural is clearly visible on a single continuous brick wall with realistic texture. "
            "The graffiti looks fresh with natural overspray and paint drips, spray mist is visible, and several unbranded "
            "spray cans lie on the ground. The person's face, body, outfit, and identity remain exactly the same, "
            "with light paint speckles only on clothes or shoes. Lighting is realistic urban daylight, shallow depth of field, "
            "and the final image is high-resolution, clean, and fully realistic with no extra people, text, or fantasy elements."
        )
    },
    "cloud_sculpture": {
        "label": "☁️ Cloud Sculpture",
        "cat": "fantasy",
        "use_master": False,
        "prompt": (
            "Using ONLY the uploaded photo as reference, transform exactly the subject shown — and no other subject — "
            "into a form made entirely of soft, billowing clouds. "
            "SUBJECT LOCK: The subject is whoever or whatever appears in the uploaded image. "
            "Do not substitute, replace, or invent a different subject. Preserve their overall silhouette and posture. "
            "CLOUD MATERIAL: The entire form must look like real cumulus clouds — fluffy, rounded, voluminous masses of white vapor. "
            "Think whipped cream or cauliflower, NOT ice, snow, marble, fur, or frozen material. "
            "CRITICAL: Every single part of the subject — body, clothing, accessories, hair, everything — must be fully transformed into cloud. "
            "No original colors, textures, patterns or materials should remain visible anywhere in the image. Pure cloud only. "
            "No sharp edges, no fine surface detail, no skin texture, no fur texture — only soft rounded cloud puffs that merge into each other. "
            "Eyes, nose, and facial features should be suggested by the shape and shadow of cloud volumes, NOT rendered with photorealistic detail. "
            "The form dissolves softly at the edges into the surrounding sky. "
            "Lighting: warm natural sunlight from above casting gentle rounded shadows within the cloud volumes. "
            "Background: bright open blue sky with a subtle gradient from deep azure at top to pale horizon. "
            "Mood: airy, weightless, dreamlike — the subject feels made of sky, not stone. "
            "Ultra-realistic cloud render quality. No text, no watermark."
        )
    },
    "artistic_style": {
        "label": "🎨 Stile Artistico",
        "cat": "fantasy",
        "use_master": False,
        "prompt": "__artistic_style__",  # placeholder — sostituito dinamicamente in _send_confirmation
    },
    "lego": {
        "label": "🧱 LEGO",
        "cat": "fantasy",
        "prompt": (
            "Ultra-photorealistic LEGO brick-built the subject, constructed entirely from authentic LEGO bricks, plates, tiles, "
            "slopes, studs and technic elements, highly detailed studded surfaces, visible seams between bricks, layered LEGO "
            "geometry forming the structure, precision LEGO building techniques, glossy ABS plastic material with subtle scratches "
            "and fingerprints, accurate plastic reflections and specular highlights, physically correct plastic translucency, "
            "vibrant molded colors, micro surface imperfections, complex brick assembly details. "
            "Dynamic cinematic advertising composition with LEGO bricks exploding, assembling, and floating around the subject, "
            "fragments suspended in mid-air, sense of motion and energy, hero product placement in the center, "
            "premium brand campaign aesthetic. "
            "Professional studio product photography lighting, softbox key light, rim light highlights, subtle bounce light, "
            "dramatic contrast, realistic soft shadows, reflective surfaces, global illumination, ray-traced reflections."
        )
    },
    "dissolve": {
        "label": "💧 Dissolvence",
        "cat": "stylistic",
        "use_master": False,
        "prompt": (
            "Portrait dissolving into fluid motion trails as if the subject is melting into liquid light. "
            "Soft painterly smears extending from facial contours, flowing movement captured in long exposure, "
            "elegant minimal background, expressive fashion portrait. "
            "CAMERA: SONY VENICE, ARRI Signature Prime 50mm. "
            "LIGHTING: soft studio lighting, luminous highlights, gentle directional light shaping the face. "
            "MOTION PHYSICS: long exposure motion smear, flowing liquid-like blur trails, continuous movement distortion. "
            "COLOR: soft neutral tones with subtle color bleed. "
            "STYLE: surreal editorial portrait, fluid temporal distortion, cinematic fine art photography."
        )
    },
    "ghost_temporal": {
        "label": "👻 Ghost Temporal",
        "cat": "stylistic",
        "use_master": False,
        "prompt": (
            "Using the uploaded photo as the identity and style reference, create an ultra-realistic 8K cinematic studio portrait "
            "framed from mid-thigh up. "
            "IDENTITY LOCK: Preserve the exact person from the photo — same face, facial structure, skin tone, hair, outfit. "
            "BACKGROUND: Vibrant ochre-red background (#C0392B), uniform but subtly graded for depth. "
            "OUTFIT: Preserve exactly the outfit worn by the subject in the uploaded photo — same garments, colors, textures, "
            "and any visible accessories. Do not replace or alter the clothing under any circumstance. "
            "POSE: Subject standing confidently, sharp focus, primary figure in full presence. "
            "GHOST EFFECT: A translucent motion-blurred ghost duplicate of the subject positioned slightly behind and to the right, "
            "streaking horizontally with colorful light trails (red, blue, yellow) conveying rapid movement or temporal distortion. "
            "The ghost is semi-transparent, 40-50% opacity, with chromatic aberration streaks. "
            "LIGHTING: Harsh frontal studio lighting, crisp shadows, emphasizing fabric textures. "
            "TECHNICAL: High-fashion editorial style, shallow depth of field on primary figure, 85mm lens feel, "
            "bold experimental avant-garde mood. 8K, ultra-sharp on primary subject. No text, no watermark."
        )
    },

    "long_exposure": {
        "label": "📸 Long Exposure",
        "cat": "stylistic",
        "use_master": False,
        "prompt": (
            "Recreate this image as a long exposure fashion photograph. "
            "TECHNIQUE: slow shutter speed (1-4 seconds), camera on tripod, subject in deliberate motion during exposure. "
            "SUBJECT: the face and upper torso retain a degree of sharpness — the core identity is recognizable — "
            "while the body, arms and hair streak into directional motion blur trails extending outward. "
            "Multiple semi-transparent ghost overlaps of the same figure suggest continuous movement through the frame. "
            "Light streaks and luminous trails follow the body contours, especially along shoulders, arms and hair. "
            "BACKGROUND: the environment (walls, furniture, candles, props) remains completely static and sharp, "
            "in high contrast with the blurred subject — this contrast is the key visual tension of the image. "
            "LIGHTING: existing ambient light sources (candles, lamps, windows) stay pinned and sharp. "
            "Their light bleeds into the motion trails of the subject creating warm luminous streaks. "
            "Candlelight or warm practical lighting preferred — intimate, cinematic, slightly dramatic. "
            "MOOD: ethereal, ghostly, cinematic fine art. The image feels like time itself has been stretched. "
            "COLOR: preserve the original color palette of the scene. Slight warm shift in the blur trails. "
            "TECHNICAL: 8K, 35-50mm lens, f/8, ISO 400, tripod-stable background, "
            "natural motion smear physics — no artificial radial blur, no zoom burst. "
            "NEGATIVE: no radial zoom blur, no fake digital motion blur overlay, no face completely lost in blur."
        )
    },

    # ── SCENOGRAFICI ─────────────────────────────────────────
    "giantess": {
        "label": "🏙️ Giantess NYC",
        "cat": "scenic",
        "prompt": (
            "A hyper-realistic photograph of a giant human subject. "
            "SCENARIO: the subject walks carefully down the center of Broadway in New York City, her sneakers spanning several "
            "city blocks while her head towers above the spire of the Chrysler Building. "
            "She is an actual human of colossal proportions (hundreds of meters tall). "
            "The environment is a real-world location with authentic textures of glass, concrete, and foliage. "
            "SUBJECT FIDELITY: exact face from reference photo, perfect facial likeness, real human skin texture, "
            "realistic human body proportions. "
            "ENVIRONMENT FIDELITY: no toys, no diorama, no miniature effect. Sharp focus throughout. "
            "LIGHTING: natural daylight, realistic atmospheric perspective, 8K resolution, shot on professional camera, "
            "extreme high resolution. Tilt-shift effect applied."
        )
    },
    "action_figure": {
        "label": "🪆 Action Figure",
        "cat": "scenic",
        "prompt": (
            "Create a 1/7 scale commercial figure of the character in the image, in a realistic style set in a real environment. "
            "The figure is placed on a computer desk and has a transparent round acrylic base. "
            "Next to the desk appears the real person from the image, life-sized and wearing the same outfit as the figure, "
            "carefully cleaning it with a fine brush, in a modern, well-lit studio. "
            "In the background, a collection of toys and action figures can be seen."
        )
    },
    "art_doll": {
        "label": "👯 Art Doll Exhibition",
        "cat": "scenic",
        "prompt": (
            "In a bright, minimalist art exhibition space, generate an oversized sculpture in the style of a 'cute big-eyed doll', "
            "with clothing style, hairstyle and accessories 100% identical to those of the person in the uploaded photo. "
            "The sculpture is 50% taller than a real person and stands naturally behind and slightly to the side of the person, "
            "ensuring the real person's face and pose do not change at all. "
            "Overall lighting and shadows are soft but well-defined; the image is clear and rich in detail, "
            "creating a cute and trendy exhibition atmosphere. Original proportions maintained."
        )
    },
    "toy_window": {
        "label": "🎎 Toy Store Window",
        "cat": "scenic",
        "prompt": (
            "Generate an ultra-realistic image based exclusively on the uploaded canvas, using its proportions and format. "
            "The scene is a bright, high-end street-fashion photograph. "
            "The subject stands in front of a luxury toy store window, delicately touching the glass with one hand. "
            "Inside the display window there is a full-size cartoon doll modeled on the subject: same features, same hair, "
            "same outfit, but rendered as a cute animated character with large eyes, stylized proportions and a 'cartoon deluxe' mood. "
            "The doll is hyper-defined with premium toy rendering. Realistic reflections on the store window, high-level fashion look, "
            "keeping the subject's real face unchanged. "
            "If the subject is an animal, a doll/puppy of the same animal will be created following the same rules. "
            "Photographic settings: f/2.8, ISO 200, 1/160s, 85mm lens, focus on torso and face, soft cinematic depth of field, "
            "natural bokeh, warm soft light, ultra-detailed glossy finish, 4.2MP output."
        )
    },

    # ── COLLAGE ───────────────────────────────────────────────
    "selfie_stick": {
        "label": "🤳 Selfie Stick POV",
        "cat": "scenic",
        "use_master": False,
        "prompt": (
            "Using the uploaded photo as identity reference, generate a new editorial photograph in selfie stick POV style. "
            "CAMERA SETUP: Extreme wide-angle fisheye perspective shot from above. The camera is mounted at the top of a selfie stick held by the subject's RIGHT hand. "
            "The camera is the one taking this photo — it cannot appear in the image. "
            "The subject's RIGHT hand grips the bottom of the stick, arm extended upward and forward. "
            "The stick extends upward from the hand and exits the frame at the top — the top of the stick and camera are NOT visible. "
            "The LEFT arm hangs naturally at the side — it does NOT hold anything. "
            "Strong fisheye barrel distortion on the edges. The subject looks up toward the lens with a natural smile. "
            "FRAMING: Bird's eye perspective — subject seen from 2-3 meters above. "
            "The environment extends dramatically in all directions. "
            "Only the bottom portion of the stick (near the hand grip) may be visible at the lower edge of the frame. "
            "IDENTITY LOCK: Preserve the exact person from the photo — same face, facial structure, skin tone, hair, outfit, shoes, accessories. "
            "SCENE: Choose one of these environments at random: "
            "a wide sandy beach with waves, a blooming wildflower meadow, a colorful city street, a mountain trail with panoramic view. "
            "TECHNICAL: GoPro/Insta360 aesthetic — vivid saturated colors, high dynamic range, sharp foreground, wide depth of field. "
            "Natural outdoor lighting. Wind-blown hair for movement. "
            "No studio lighting, no bokeh, no portrait framing, no eye-level camera. Cinematic 1:1 aspect ratio. "
            "Ultra-realistic, high detail, no text, no watermark."
        )
    },

    # ── COLLAGE ───────────────────────────────────────────────
    "new_pose": {
        "label": "🆕 New Pose",
        "cat": "collage",
        "prompt": (
            "Create a new image using the exact same prompt, scene, outfit and identity as the reference, "
            "but with a completely different, natural and editorial pose and a different facial expression."
        )
    },
    "triple_set": {
        "label": "3️⃣× Triple Set",
        "cat": "collage",
        "prompt": (
            "Generate a set of 3 separate and different images in high resolution, using the uploaded image as base, "
            "changing pose but maintaining its original aspect ratio and exact proportions. Seed: random for each."
        )
    },
    "triptych": {
        "label": "3️⃣❌1️⃣ Triptych GHI",
        "cat": "altri",
        "prompt": (
            "Create a 3:1 collage of three versions with completely different poses and facial expressions of the same prompt, seed: random. "
            "Version 1: Glossy — hyper-glamour rendering, pearlescent iridescent aesthetics, mirror-gloss surfaces, angel couture runway effect. "
            "Version 2: HDR+ — powerful neon light sources along hair, clothes and background edges, cyan, magenta and lime glow, "
            "HDR long-exposure neon style, face and eyes sharp and realistic. "
            "Version 3: Holographic — dichroic refraction spectrum shifting between electric teal, deep cosmic blue and fiery metallic orange, "
            "prismatic light dispersion, holographic shimmer on all non-skin surfaces."
        )
    },
    "pastel_clones": {
        "label": "🌸 Pastel Clones",
        "cat": "collage",
        "use_master": False,
        "prompt": (
            "Ultra-realistic high-fashion editorial collage with 7 clones of the subject from the provided reference image. "
            "Preserve the subject's face, identity and physical features EXACTLY as they appear in the reference — "
            "do not alter facial structure, expression, skin texture, beard, glasses or proportions. "
            "OUTFIT: Each clone wears the EXACT same outfit as in the reference image — same garments, same colors, same cut, same accessories. "
            "Do not substitute or invent new clothing. The outfit is fixed and must be reproduced faithfully in every clone. "
            "PASTEL TREATMENT — apply ONLY to: background colors, studio lighting palette, props, set elements, "
            "background panels, floor surfaces, decorative objects. "
            "Palette: blush pink, powder blue, mint green, lilac, cream — soft geometric color block background panels. "
            "The subject's outfit and skin tones are NOT pastelized — they remain true to the reference. "
            "Layout: luxury fashion magazine spread, structured layered depth, foreground/midground/background separation. "
            "7 poses distributed across the frame — varied: standing, seated, lying, walking, cross-legged, playful, relaxed. "
            "Layered torn paper collage textures, floating petals. "
            "Soft diffused beauty lighting with subtle rim light, cinematic glow highlights. "
            "85mm portrait lens, ultra-detailed, sharp focus on all faces, subtle film grain, pastel light leaks. Ratio 9:16."
        )
    },
    "collage_2x2": {
        "label": "🟦 Collage 2×2",
        "cat": "collage",
        "use_master": False,
        "prompt": (
            "Using the uploaded photo as the identity and style reference, create a 2×2 quad-panel collage "
            "of the same subject with four completely different camera angles and poses. "
            "IDENTITY LOCK: Preserve the exact person from the photo — same face, facial structure, skin tone, hair, "
            "outfit, accessories, and any distinctive elements visible in the image. "
            "All four panels must show the same person from the photo, consistently. "
            "Each panel has a distinct framing and perspective — no two panels may share the same angle or pose. "
            "Top-left panel: camera positioned low, angled upward, subject has one hand on hip the other extended toward the lens. "
            "Top-right panel: extreme high-angle bird's eye view looking straight down, subject gazes up at camera one arm reaching upward. "
            "Bottom-left panel: full-length shot with tilted horizon, subject in three-quarter profile highlighting silhouette. "
            "Bottom-right panel: shot from behind and slightly to the side, subject looks back over the shoulder toward the camera. "
            "Adapt the lighting and environment from the reference photo across all four panels. "
            "Consistent subject identity, outfit, and color grade across all panels. "
            "Thin dark dividing lines between panels. Unified cinematic look. "
        )
    },
    "photobooth_4x4": {
        "label": "📷 Photobooth 4×4",
        "cat": "collage",
        "use_master": False,
        "prompt": (
            "Using the uploaded photo as the identity and style reference, create a color photobooth expression grid "
            "with a 4x4 layout of 16 panels. "
            "IDENTITY LOCK: Preserve the exact person from the photo — same face, facial structure, skin tone, hair, "
            "makeup, accessories, jewelry, props and any distinctive elements visible in the image. "
            "If the photo shows makeup, earrings, props (fruit, objects, etc.), wet hair, or any distinctive styling — "
            "replicate all of these consistently across every single panel. "
            "SETTING: Use the same background environment and lighting mood from the reference photo, "
            "adapted to a tight head-and-shoulders photobooth framing. "
            "Eyes sharp in every panel. Natural realistic skin tones. Medium to high contrast. "
            "Subtle authentic analog photobooth grain in color. Thin gutters between panels. High panel consistency. "
            "50mm lens look. Tight head and shoulders framing. "
            "16 expressions in order: 1-scrunched smile eyes slightly squeezed, 2-intense stare fingers framing eyes, "
            "3-big joyful laugh mouth open, 4-bored unimpressed chin in hands, 5-sad pout watery eyes, "
            "6-goofy face hands making small horns above head, 7-playful tongue out cheeky grin, "
            "8-angry glare eyebrows down, 9-flirty look hand touching cheek, 10-surprised wide eyes mouth slightly open, "
            "11-excited shout hands near face, 12-mischievous grin claw-like hand pose, "
            "13-confused frown lips pressed, 14-dramatic crying hands on head, "
            "15-tongue out eyes closed playful, 16-duck face with small devil horns gesture. "
            "Ultra high resolution, photorealistic color photobooth contact sheet aesthetic. "
            "No extra fingers, no missing fingers, no deformed hands, no warped face, no uneven eyes, "
            "no melted mouth, no plastic skin, no text, no watermark, no blur."
        )
    },
    "fullbody_3x3": {
        "label": "🧍 Full Body 3×3",
        "cat": "collage",
        "use_master": False,
        "prompt": lambda: __import__('random').sample([
            "confident frontal stance hands on hips direct gaze",
            "three-quarter turn left hand on waist looking over shoulder",
            "full rear view looking back at camera",
            "low angle shot from below dramatic perspective subject looking down at camera",
            "side profile elegant posture chin slightly raised",
            "dynamic walking pose mid-stride natural movement",
            "seated on floor legs extended arms behind relaxed editorial pose",
            "leaning against wall one foot raised casual elegant",
            "arms raised overhead full body stretch triumphant pose",
            "crossed arms power stance slight smirk direct gaze",
            "one hand on chin thoughtful elegant pose",
            "mid-turn caught in movement hair and outfit in motion",
            "crouching low dramatic editorial crouch arms resting on knees",
            "leaning forward toward camera hands on thighs intimate editorial",
            "back against wall arms wide open dramatic silhouette",
        ], 9),
    },

    # ── PET ──────────────────────────────────────────────────────
    "pet_mosaic": {
        "label": "🐾 Pet Mosaic 4×4",
        "cat": "altri",
        "use_master": False,
        "prompt": (
            "Using the uploaded photo as the identity reference, create a color expression grid "
            "with EXACTLY 4 columns and 4 rows — 16 panels total, square or landscape orientation. "
            "The grid MUST be 4 wide by 4 tall. Not 3x5, not 3x4, not any other layout — strictly 4x4. "
            "IDENTITY LOCK: Preserve the exact animal from the photo — same breed, fur color, fur texture, "
            "eye color, size, markings, and any distinctive features. Same animal in every single panel. "
            "SETTING: Plain neutral light gray backdrop, soft even studio lighting, tight head and shoulders framing. "
            "50mm lens look. Eyes sharp in every panel. Natural realistic fur texture and skin tones. "
            "Medium to high contrast. Subtle authentic analog grain. Thin gutters between panels. High panel consistency. "
            "16 animal expressions and poses in order: "
            "1-happy panting tongue out wide smile, "
            "2-ears perked up alert and curious staring at camera, "
            "3-head tilted sideways maximum confusion, "
            "4-yawning big mouth open eyes squinting, "
            "5-sleepy half-closed eyes drowsy expression, "
            "6-playful bow front legs down ready to play, "
            "7-grumpy serious unimpressed face, "
            "8-surprised wide eyes startled expression, "
            "9-sniffing nose forward intense concentration, "
            "10-excited bouncy energy sparkling eyes, "
            "11-begging puppy eyes maximum cuteness irresistible stare, "
            "12-caught doing something naughty guilty face ears back, "
            "13-dramatic sad face watery eyes pout, "
            "14-fierce mock growl showing teeth playfully, "
            "15-blep tiny tongue barely sticking out, "
            "16-ridiculous goofy face with small devil horns. "
            "Ultra high resolution photorealistic animal portrait contact sheet aesthetic. "
            "No deformed snout, no wrong number of legs, no anatomical errors, no text, no watermark, no blur."
        )
    },
}

# Categorie e ordine
CATEGORIES = {
    "stylistic": "🎨 Stilistici",
    "fantasy":   "✨ Fantasy & Art",
    "scenic":    "🏙️ Scenografici",
    "collage":   "🖼️ Collage",
    "mosaic":    "🖼️ Mosaic",
    "altri":     "✨ Altri",
}

def filters_by_cat(cat):
    return {k: v for k, v in FILTERS.items() if v["cat"] == cat}

# ============================================================
# BOT
# ============================================================
telebot.apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", use_class_middlewares=True)

# --- WHITELIST MIDDLEWARE ---
@bot.middleware_handler(update_types=['message', 'callback_query'])
def check_whitelist(bot_instance, update):
    if hasattr(update, 'from_user'):
        uid = update.from_user.id
    elif hasattr(update, 'message') and update.message:
        uid = update.message.from_user.id
    else:
        return
    if not is_allowed(uid):
        logger.warning(f"🚫 Accesso non autorizzato bloccato: uid={uid}")
        raise telebot.CancelUpdate()

# --- KEYBOARD CATEGORIE ---
def cat_keyboard():
    markup = types.InlineKeyboardMarkup()
    for cat_key, cat_label in CATEGORIES.items():
        if cat_key == "mosaic":
            markup.add(types.InlineKeyboardButton(cat_label, callback_data="mosaic_start"))
        else:
            markup.add(types.InlineKeyboardButton(cat_label, callback_data=f"cat_{cat_key}"))
    return markup

# --- KEYBOARD FILTRI ---
def filter_keyboard(cat):
    markup = types.InlineKeyboardMarkup()
    for fkey, fdata in filters_by_cat(cat).items():
        markup.add(types.InlineKeyboardButton(fdata["label"], callback_data=f"f_{fkey}"))
    markup.add(types.InlineKeyboardButton("◀️ Indietro", callback_data="back_cats"))
    return markup

# --- /start ---
@bot.message_handler(commands=['start', 'reset'])
def cmd_start(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /start non autorizzato: uid={uid} username={m.from_user.username}")
        return
    username = m.from_user.username or m.from_user.first_name
    # Reset completo di tutti gli stati
    user_filter[uid] = None
    user_category[uid] = None
    pending.pop(uid, None)
    last_img.pop(uid, None)
    last_prompt.pop(uid, None)
    pending_artistic_style.pop(uid, None)
    stereo_waiting.pop(uid, None)
    stereo_last_img.pop(uid, None)
    mirror_waiting.pop(uid, None)
    mirror_last_img.pop(uid, None)
    mirror_pending_prompt.pop(uid, None)
    if uid in mosaic_collecting:
        session = mosaic_collecting.pop(uid)
        if session.get('timer'):
            try: session['timer'].cancel()
            except Exception: pass
    logger.info(f"🔄 /start da {username} (id={uid})")
    bot.send_message(m.chat.id, "✅ <b>Reset completo.</b> Tutte le sessioni cancellate.")
    bot.send_message(m.chat.id,
        f"<b>🎨 Filtro v{VERSION}</b>\n\n"
        f"Invia una foto e scegli un filtro.\n"
        f"Usa /filtro per scegliere il filtro prima della foto, o invia la foto direttamente.",
        reply_markup=cat_keyboard()
    )

# --- /filtro ---
@bot.message_handler(commands=['filtro', 'filter'])
def cmd_filtro(m):
    uid = m.from_user.id
    logger.info(f"🎨 /filtro da {m.from_user.username or m.from_user.first_name} (id={uid})")
    bot.send_message(m.chat.id, "🎨 <b>Scegli una categoria:</b>", reply_markup=cat_keyboard())

# --- /help ---
@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        f"<b>🎨 Filtro v{VERSION} — Comandi</b>\n\n"
        f"/start · /reset — Reset e menu principale\n"
        f"/filtro — Scegli filtro prima della foto\n"
        f"/mosaic — Avvia sessione mosaic (2-9 foto)\n"
        f"/done — Conclude sessione mosaic\n"
        f"/caption — Genera caption da foto\n"
        f"/lastprompt — Ultimo prompt inviato\n"
        f"/info — Versione e informazioni\n"
        f"/help — Questo messaggio\n\n"
        f"<i>Invia una foto per iniziare.</i>"
    )

# --- /info ---
@bot.message_handler(commands=['info'])
def cmd_info(m):
    uid = m.from_user.id
    fkey = user_filter[uid]
    fname = FILTERS[fkey]["label"] if fkey else "Nessuno"
    bot.send_message(m.chat.id,
        f"<b>🎨 Filtro v{VERSION}</b>\n\n"
        f"Filtro attivo: <b>{fname}</b>\n"
        f"Categorie: Stilistici · Fantasy & Art · Scenografici · Collage · Mosaic · Altri\n"
        f"Comandi: /help per la lista completa"
    )

@bot.message_handler(commands=['lastprompt'])
def cmd_lastprompt(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"🔍 /lastprompt da {username} (id={uid})")
    prompt = last_prompt.get(uid)
    if not prompt:
        bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile. Genera prima un'immagine.")
        return
    chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
    for idx, chunk in enumerate(chunks):
        header = f"🔍 <b>Ultimo prompt inviato all'API</b> ({idx+1}/{len(chunks)}):\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
        bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")

# --- CALLBACK POST-GENERAZIONE ---
@bot.callback_query_handler(func=lambda c: c.data in ["post_newfilter", "post_newphoto", "post_newboth", "post_retry"])
def handle_post(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass

    if call.data == "post_retry":
        # Stesso filtro, stessa foto
        fkey = user_filter.get(uid)
        img = last_img.get(uid)
        if not fkey or not img:
            bot.send_message(call.message.chat.id, "⚠️ Nessun dato da ripetere. Invia una nuova foto.")
            return
        fname = FILTERS[fkey]["label"]
        logger.info(f"🔁 {username} → riprova stesso filtro ({fkey}), stessa foto")
        bot.send_message(call.message.chat.id, f"🔁 <b>Riprovo {fname}...</b>")
        data = {'filter_key': fkey, 'img': img}
        executor.submit(_run_generation, call.message.chat.id, uid, username, data)
        return

    if call.data == "post_newfilter":
        # Stessa foto, nuovo filtro — resetta solo il filtro
        if uid in last_img:
            pending[uid] = {'img': last_img[uid], 'filter_key': None}
        user_filter[uid] = None
        logger.info(f"🔄 {username} → nuovo filtro, stessa foto")
        bot.send_message(call.message.chat.id, "🎨 <b>Scegli il nuovo filtro:</b>", reply_markup=cat_keyboard())

    elif call.data == "post_newphoto":
        # Stesso filtro, nuova foto
        fkey = user_filter[uid]
        if not fkey:
            bot.send_message(call.message.chat.id, "⚠️ Nessun filtro attivo. Scegli un filtro prima.", reply_markup=cat_keyboard())
            return
        fname = FILTERS[fkey]["label"]
        logger.info(f"🔄 {username} → stesso filtro ({fkey}), nuova foto")
        bot.send_message(call.message.chat.id,
            f"📷 Filtro attivo: <b>{fname}</b>\n\nInvia la nuova foto da elaborare.")

    elif call.data == "post_newboth":
        # Nuova foto E nuovo filtro — reset completo
        user_filter[uid] = None
        user_category[uid] = None
        pending.pop(uid, None)
        logger.info(f"🔄 {username} → nuova foto e nuovo filtro")
        bot.send_message(call.message.chat.id,
            "🆕 <b>Ricominciamo!</b>\n\nInvia una nuova foto e scegli un nuovo filtro.",
            reply_markup=cat_keyboard())

# --- CALLBACK CATEGORIE ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("cat_") or c.data == "back_cats")
def handle_cat(call):
    uid = call.from_user.id
    if call.data == "back_cats":
        try:
            bot.edit_message_text("🎨 <b>Scegli una categoria:</b>",
                call.message.chat.id, call.message.message_id,
                reply_markup=cat_keyboard(), parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, "🎨 <b>Scegli una categoria:</b>",
                reply_markup=cat_keyboard())
        return

    cat = call.data.replace("cat_", "")
    user_category[uid] = cat

    # Categoria "altri" ha anche 3D e Mirror che non sono in FILTERS
    if cat == "altri":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎥 3D Stereo", callback_data="stereo_start"))
        markup.add(types.InlineKeyboardButton("🪞 Mirror Outfits", callback_data="mirror_start"))
        for fkey, fdata in filters_by_cat("altri").items():
            markup.add(types.InlineKeyboardButton(fdata["label"], callback_data=f"f_{fkey}"))
        markup.add(types.InlineKeyboardButton("◀️ Indietro", callback_data="back_cats"))
        try:
            bot.edit_message_text("✨ <b>Altri</b> — scegli il filtro:",
                call.message.chat.id, call.message.message_id,
                reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, "✨ <b>Altri</b> — scegli il filtro:",
                reply_markup=markup)
        return

    cat_label = CATEGORIES.get(cat, cat)
    try:
        bot.edit_message_text(f"🎨 <b>{cat_label}</b> — scegli il filtro:",
            call.message.chat.id, call.message.message_id,
            reply_markup=filter_keyboard(cat), parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, f"🎨 <b>{cat_label}</b> — scegli il filtro:",
            reply_markup=filter_keyboard(cat))

# --- CALLBACK FILTRI ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("f_"))
def handle_filter(call):
    uid = call.from_user.id
    fkey = call.data.replace("f_", "")
    if fkey not in FILTERS:
        bot.answer_callback_query(call.id, "Filtro non trovato.")
        return

    user_filter[uid] = fkey
    fname = FILTERS[fkey]["label"]
    bot.answer_callback_query(call.id, f"✅ {fname}")
    logger.info(f"🎨 {call.from_user.username or call.from_user.first_name} (id={uid}) → filtro: {fkey}")

    # Pulisce sessione mosaic zombie se presente
    if uid in mosaic_collecting:
        session = mosaic_collecting.pop(uid)
        if session.get("timer"):
            session["timer"].cancel()
        logger.info(f"   🧹 Sessione mosaic zombie rimossa per uid={uid}")

    # Se c'è già un'immagine in attesa, prepara subito la conferma
    if uid in pending and pending[uid].get('img'):
        pending[uid]['filter_key'] = fkey
        _send_confirmation(call.message.chat.id, uid, fname)
    else:
        try:
            bot.edit_message_text(
                f"✅ Filtro selezionato: <b>{fname}</b>\n\nOra invia la foto da elaborare.",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id,
                f"✅ Filtro selezionato: <b>{fname}</b>\n\nOra invia la foto da elaborare.")

# --- CALLBACK CONFERMA / ANNULLA ---
@bot.callback_query_handler(func=lambda c: c.data in ["confirm_fx", "cancel_fx"])
def handle_confirm(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass

    if call.data == "cancel_fx":
        pending.pop(uid, None)
        logger.info(f"❌ {username} ha annullato.")
        bot.send_message(call.message.chat.id, "❌ <b>Annullato.</b>")
        return

    data = pending.get(uid)
    if not data or not data.get('img') or not data.get('filter_key'):
        bot.send_message(call.message.chat.id, "⚠️ Sessione scaduta. Invia di nuovo la foto.")
        return

    fkey = data['filter_key']
    fname = FILTERS[fkey]["label"]
    logger.info(f"🚀 {username} (id={uid}) → generazione | filtro: {fkey}")

    # Caption generata subito dal testo — disponibile anche se la generazione fallisce
    filter_prompt_pre = FILTERS[fkey].get("prompt", "")

    bot.send_message(call.message.chat.id,
        f"🚀 <b>Generazione avviata!</b>\n"
        f"🎨 Filtro: <b>{fname}</b>\n"
        f"⏳ Attendi ~20–35 secondi.")

    executor.submit(_run_generation, call.message.chat.id, uid, username, data)
    pending.pop(uid, None)


# --- 3D STEREO ---
STEREO_PROMPT = (
    "Analyze the provided image carefully. "
    "Recreate it as a single composite image in 21:9 aspect ratio divided into exactly two equal panels side by side, "
    "designed for cross-eyed stereoscopic 3D viewing.\n\n"
    "LEFT PANEL — right-eye view: recreate the scene with the virtual camera shifted approximately 6cm to the RIGHT. "
    "All lighting, colors, textures and subject identity must remain identical to the original.\n\n"
    "RIGHT PANEL — left-eye view: recreate the exact same scene with the virtual camera shifted approximately 6cm to the LEFT.\n\n"
    "CRITICAL RULES:\n"
    "- Each panel occupies exactly half the total 21:9 width\n"
    "- Foreground elements must show MORE horizontal shift than background elements — this creates natural depth parallax\n"
    "- Background elements shift less; distant elements shift the least\n"
    "- Both panels are photorealistic and visually identical except for the horizontal perspective shift\n"
    "- No color separation, no anaglyph effect, no red/cyan tinting\n"
    "- No visible seam or border between the two panels\n"
    "- Cross-eyed viewing: when the viewer crosses their eyes, the two panels must converge into a single 3D image with natural perceived depth\n"
    "- Maintain all original details: lighting, colors, textures, subject identity, mood\n"
    "- Do NOT add watermarks or text"
)

stereo_waiting = {}  # uid → True se in attesa di foto

@bot.callback_query_handler(func=lambda c: c.data == "stereo_start")
def handle_stereo_start(call):
    uid = call.from_user.id
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    stereo_waiting[uid] = True
    bot.send_message(call.message.chat.id,
        "🎥 <b>3D Stereo</b>\n\n"
        "Invia la foto da convertire in stereoscopico cross-eyed.\n"
        "Funziona meglio con soggetti in primo piano su sfondo distante.")

def _run_stereo(chat_id, uid, username, img_bytes):
    t_start = time.time()
    logger.info(f"   🎥 Stereo richiesto da {username} — generazione immagini rimossa, invio prompt Flow")
    try:
        full_prompt = STEREO_PROMPT
        last_prompt[uid] = full_prompt
        elapsed = round(time.time() - t_start, 1)
        result_markup = types.InlineKeyboardMarkup()
        result_markup.add(types.InlineKeyboardButton("📷 Nuova foto", callback_data="stereo_start"))
        result_markup.add(types.InlineKeyboardButton("🏠 Menu principale", callback_data="stereo_menu"))
        bot.send_message(chat_id, "⚡ <b>Prompt Stereo pronto.</b> Usa Flow per generare.")
        chunks = [full_prompt[i:i+3800] for i in range(0, len(full_prompt), 3800)]
        for idx, chunk in enumerate(chunks):
            header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
            if idx == len(chunks) - 1:
                bot.send_message(chat_id, f"{header}<code>{html.escape(chunk)}</code>", reply_markup=result_markup)
            else:
                bot.send_message(chat_id, f"{header}<code>{html.escape(chunk)}</code>")
        logger.info(f"   ✅ Prompt stereo inviato a {username} in {elapsed}s")
    except Exception as e:
        elapsed = round(time.time() - t_start, 1)
        logger.error(f"   ❌ Errore stereo: {e}", exc_info=True)
        bot.send_message(chat_id, f"❌ Errore interno ({elapsed}s):\n<code>{html.escape(str(e))}</code>")

stereo_last_img = {}  # uid → img_bytes per retry

# --- MIRROR OUTFITS ---

def _build_mirror_prompt(img_bytes):
    """Genera il prompt Mirror: 4 riflessi speculari della stessa foto, outfit invariato."""
    return (
        "STEP 1 — MANDATORY OUTFIT ANALYSIS: Before generating anything, carefully examine the provided image "
        "and write a precise internal description of the subject's complete outfit: every garment (name, color, fabric, "
        "cut, coverage), every accessory (jewelry, shoes, bags, hats), and every visible styling detail. "
        "This outfit description is LOCKED and must be reproduced identically in all 4 mirror panels. "
        "DO NOT alter, replace, remove or add any garment or accessory.\n\n"
        "CRITICAL — THE SUBJECT MUST ALWAYS BE FULLY CLOTHED IN ALL 4 PANELS. "
        "The outfit from the photo is MANDATORY. Generating the subject without clothing is strictly forbidden.\n\n"
        "STEP 2 — IMAGE GENERATION: Generate a single photorealistic image showing a luxury vanity dressing room. "
        "On the makeup table sits a makeup mirror composed of exactly 4 SEPARATE FLAT PANELS arranged side by side, "
        "each panel slightly angled approximately 20 degrees from the next, like a polyptych. "
        "There is NO center panel — all 4 panels are equal in size and clearly distinct. "
        "The subject is seen from behind in the foreground, sitting at the vanity, slightly out of focus.\n\n"
        "Each of the 4 mirror panels MUST show the subject wearing the EXACT SAME OUTFIT from the photo — "
        "identical garments, identical colors, identical accessories, no exceptions, no substitutions.\n\n"
        "The 4 panels differ ONLY in:\n"
        "- Slight angle variation (each panel reflects a marginally different viewpoint)\n"
        "- Subtle expression change (neutral / slight smile / eyes down / eyes up)\n"
        "- Minor head or shoulder pose shift — NEVER a different outfit, NEVER without clothing\n\n"
        "TECHNICAL REQUIREMENTS:\n"
        "- Warm Hollywood vanity lighting with round bulbs framing the mirror\n"
        "- Each panel is a distinct flat mirror — no curved or folding mirrors\n"
        "- Correct mirror reflections with natural perspective for each angle\n"
        "- Subject from behind in foreground is partially visible, out of focus\n"
        "- Each panel reflection is sharp, clearly shows face AND full outfit\n"
        "- Elegant, cinematic atmosphere — luxury dressing room\n"
        "- 8K resolution, 4:3 format\n"
        "- No text, no watermarks"
    )

@bot.callback_query_handler(func=lambda c: c.data in ["stereo_retry", "stereo_menu"])
def handle_stereo_post(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    if call.data == "stereo_menu":
        bot.send_message(call.message.chat.id, "🎨 <b>Scegli una categoria:</b>", reply_markup=cat_keyboard())
        return
    # stereo_retry
    img_bytes = stereo_last_img.get(uid)
    if not img_bytes:
        bot.send_message(call.message.chat.id, "⚠️ Sessione scaduta. Invia di nuovo la foto.")
        stereo_waiting[uid] = True
        return
    bot.send_message(call.message.chat.id, "🔁 Riprovo la stessa foto...\n⏳ Attendi ~30 secondi.")
    executor.submit(_run_stereo, call.message.chat.id, uid, username, img_bytes)

mirror_waiting = {}   # uid → True
mirror_last_img = {}  # uid → img_bytes per retry
mirror_pending_prompt = {}  # uid → prompt string

@bot.callback_query_handler(func=lambda c: c.data == "mirror_confirm")
def handle_mirror_confirm(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    img_bytes = mirror_last_img.get(uid)
    if not img_bytes:
        bot.send_message(call.message.chat.id, "⚠️ Sessione scaduta. Invia di nuovo la foto.")
        return
    bot.send_message(call.message.chat.id, "🪞 <b>Mirror Outfits avviato!</b>\n⏳ Attendi ~30 secondi.")
    executor.submit(_run_mirror, call.message.chat.id, uid, username, img_bytes)

@bot.callback_query_handler(func=lambda c: c.data == "altri_menu")
def handle_altri_menu(call):
    uid = call.from_user.id
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎥 3D Stereo", callback_data="stereo_start"))
    markup.add(types.InlineKeyboardButton("🪞 Mirror Outfits", callback_data="mirror_start"))
    for fkey, fdata in filters_by_cat("altri").items():
        markup.add(types.InlineKeyboardButton(fdata["label"], callback_data=f"f_{fkey}"))
    markup.add(types.InlineKeyboardButton("◀️ Indietro", callback_data="back_cats"))
    bot.send_message(call.message.chat.id, "✨ <b>Altri filtri:</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "mirror_start")
def handle_mirror_start(call):
    uid = call.from_user.id
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    mirror_waiting[uid] = True
    bot.send_message(call.message.chat.id,
        "🪞 <b>Mirror Outfits</b>\n\n"
        "Invia una foto del soggetto.\n"
        "Genererò 4 riflessi allo specchio della stessa foto, con lo stesso outfit.")

def _run_mirror(chat_id, uid, username, img_bytes):
    t_start = time.time()
    logger.info(f"   🪞 Mirror Outfits | {username} — generazione rimossa, invio prompt Flow")
    try:
        prompt = _build_mirror_prompt(img_bytes)
        last_prompt[uid] = prompt
        elapsed = round(time.time() - t_start, 1)
        result_markup = types.InlineKeyboardMarkup()
        result_markup.add(types.InlineKeyboardButton("📷 Nuova foto", callback_data="mirror_start"))
        result_markup.add(types.InlineKeyboardButton("🏠 Menu principale", callback_data="mirror_menu"))
        bot.send_message(chat_id, "⚡ <b>Prompt Mirror pronto.</b> Usa Flow per generare.")
        chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
        for idx, chunk in enumerate(chunks):
            header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
            if idx == len(chunks) - 1:
                bot.send_message(chat_id, f"{header}<code>{html.escape(chunk)}</code>", reply_markup=result_markup)
            else:
                bot.send_message(chat_id, f"{header}<code>{html.escape(chunk)}</code>")
        logger.info(f"   ✅ Prompt mirror inviato a {username} in {elapsed}s")
    except Exception as e:
        elapsed = round(time.time() - t_start, 1)
        logger.error(f"   ❌ Errore mirror: {e}", exc_info=True)
        bot.send_message(chat_id, f"❌ Errore interno ({elapsed}s):\n<code>{html.escape(str(e))}</code>")

@bot.callback_query_handler(func=lambda c: c.data in ["mirror_retry", "mirror_menu"])
def handle_mirror_post(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    if call.data == "mirror_menu":
        bot.send_message(call.message.chat.id, "🎨 <b>Scegli una categoria:</b>", reply_markup=cat_keyboard())
        return
    img_bytes = mirror_last_img.get(uid)
    if not img_bytes:
        bot.send_message(call.message.chat.id, "⚠️ Sessione scaduta. Invia di nuovo la foto.")
        mirror_waiting[uid] = True
        return
    bot.send_message(call.message.chat.id, "🔁 Riprovo con nuovi outfit...\n⏳ Attendi ~30 secondi.")
    executor.submit(_run_mirror, call.message.chat.id, uid, username, img_bytes)
@bot.callback_query_handler(func=lambda c: c.data.startswith("mosaic_build_"))
def handle_mosaic_build(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if uid not in mosaic_collecting:
        bot.send_message(call.message.chat.id, "⚠️ Sessione mosaic scaduta. Usa /mosaic per ricominciare.")
        return
    executor.submit(_finalize_mosaic, uid, call.message.chat.id)

# --- /caption standalone ---
@bot.message_handler(commands=['caption'])
def cmd_caption(m):
    uid = m.from_user.id
    img = last_img.get(uid)
    if not img:
        bot.send_message(m.chat.id, "📸 Invia prima una foto, poi usa /caption.")
        return
    wait = bot.send_message(m.chat.id, "✍️ Genero caption...")
    result, err = caption.from_image(img)
    try: bot.delete_message(m.chat.id, wait.message_id)
    except Exception: pass
    if result:
        bot.send_message(m.chat.id, result)
    else:
        bot.send_message(m.chat.id, err or "⚠️ Caption non disponibile.")

# --- MOSAIC ---
def _start_mosaic_session(uid, chat_id, username):
    if uid in mosaic_collecting and mosaic_collecting[uid].get('timer'):
        mosaic_collecting[uid]['timer'].cancel()
    mosaic_collecting[uid] = {'photos': [], 'timer': None, 'aspect': None}
    logger.info(f"🖼️ Mosaic avviato da {username} (id={uid})")
    bot.send_message(chat_id,
        "🖼️ <b>Modalità Mosaic attiva!</b>\n\n"
        "Invia da <b>2 a 9 foto</b> e premi <b>✅ Procedi</b> quando vuoi.\n"
        "⏱️ La sessione scade automaticamente dopo 5 minuti di inattività."
    )

@bot.message_handler(commands=['mosaic'])
def cmd_mosaic(m):
    _start_mosaic_session(m.from_user.id, m.chat.id, m.from_user.username or m.from_user.first_name)

@bot.callback_query_handler(func=lambda c: c.data == "mosaic_start")
def cb_mosaic_start(call):
    uid = call.from_user.id
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception: pass
    _start_mosaic_session(uid, call.message.chat.id, call.from_user.username or call.from_user.first_name)

@bot.message_handler(commands=['done'])
def cmd_done(m):
    uid = m.from_user.id
    if uid not in mosaic_collecting:
        bot.send_message(m.chat.id, "⚠️ Nessuna sessione mosaic attiva. Usa /mosaic per iniziare.")
        return
    executor.submit(_finalize_mosaic, uid, m.chat.id)

def _detect_aspect_label(w, h):
    ratio = w / h
    if ratio > 1.6:
        return "16:9"
    elif ratio > 1.1:
        return "4:3"
    elif ratio > 0.85:
        return "1:1"
    elif ratio > 0.55:
        return "3:4"
    else:
        return "9:16"

def _finalize_mosaic(uid, chat_id):
    data = mosaic_collecting.pop(uid, None)
    if not data:
        return
    if data.get('timer'):
        data['timer'].cancel()

    photos = data['photos']
    n = len(photos)
    aspect_label = data.get('aspect', '1:1')

    if n < 2:
        bot.send_message(chat_id, "⚠️ Servono almeno 2 foto per il collage.")
        return

    # Layout per N=3 dipende dall'aspect ratio
    IS_VERTICAL = aspect_label in ("9:16", "3:4")
    IS_HORIZONTAL = aspect_label in ("16:9", "4:3")

    # LAYOUTS: lista di righe, ogni riga = numero di colonne
    if n == 3:
        layout = None  # gestito separatamente: 1 grande (2/3) + 2 piccole (1/3)
    elif n == 2:
        if IS_HORIZONTAL:
            layout = [(1,), (1,)]  # 2 impilate → verticale
        else:
            layout = [(2,)]        # 2 affiancate → orizzontale
    else:
        LAYOUTS = {
            4: None,  # gestito separatamente: 1 grande + 3 piccole
            5: [(2,), (3,)],
            6: [(3,), (3,)],
            7: [(3,), (4,)],
            8: [(4,), (4,)],
            9: [(3,), (3,), (3,)],
        }
        layout = LAYOUTS[n]

    if n == 3:
        grid_label = "1+2"
    elif n == 4:
        grid_label = "1+3"
    elif n == 6:
        grid_label = "2×3"
    elif n == 8:
        grid_label = "2×4"
    elif n == 9:
        grid_label = "3×3"
    else:
        grid_label = "+".join(str(r[0]) for r in layout)

    bot.send_message(chat_id, f"🖼️ Assemblando collage {grid_label} ({aspect_label})...")

    def get_border_color(img):
        """Colore medio dei 4 bordi — campiona su resize 50px per velocità."""
        small = img.resize((50, 50), Image.BOX)
        w, h = small.size
        pixels = []
        for x in range(w):
            pixels.append(small.getpixel((x, 0)))
            pixels.append(small.getpixel((x, h - 1)))
        for y in range(h):
            pixels.append(small.getpixel((0, y)))
            pixels.append(small.getpixel((w - 1, y)))
        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)
        return (r, g, b)

    def fit_tile(img, tw, th):
        """Scala mantenendo aspect ratio, bande con colore bordi."""
        ratio = min(tw / img.width, th / img.height)
        new_w = int(img.width * ratio)
        new_h = int(img.height * ratio)
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        bg_color = get_border_color(img)
        tile = Image.new("RGB", (tw, th), bg_color)
        tile.paste(img_resized, ((tw - new_w) // 2, (th - new_h) // 2))
        return tile

    def build():
        try:
            images = [Image.open(io.BytesIO(b)).convert("RGB") for b in photos]

            ref = images[0]
            orig_w, orig_h = ref.width, ref.height
            photo_ratio = orig_h / orig_w  # es. 2496/1664 ≈ 1.5

            # Target grid ~4Mpx — calcolo dimensioni da target, non dalle foto originali
            TARGET_PX = 4_000_000

            # Casi speciali n=3 / n=4: 1 grande + colonna/riga di piccole con rapporto geometrico esatto
            if n in (3, 4):
                k = n - 1
                # TARGET = (k * small_w) * ((k + 1) * small_h) = k*(k+1)*small_w^2*photo_ratio
                small_w = max(1, int((TARGET_PX / (k * (k + 1) * photo_ratio)) ** 0.5))
                small_h = max(1, int(small_w * photo_ratio))
                bg = get_border_color(images[0])

                if IS_HORIZONTAL:
                    # 1 grande sopra, k piccole sotto; ogni piccola ha larghezza = 1/k della grande
                    total_w = k * small_w
                    big_h = k * small_h
                    total_h = big_h + small_h
                    grid = Image.new("RGB", (total_w, total_h), bg)
                    grid.paste(fit_tile(images[0], total_w, big_h), (0, 0))
                    for i, img in enumerate(images[1:n]):
                        grid.paste(fit_tile(img, small_w, small_h), (i * small_w, big_h))
                else:
                    # 1 grande a sinistra, k piccole a destra; ogni piccola ha altezza = 1/k della grande
                    big_w = k * small_w
                    total_w = big_w + small_w
                    total_h = k * small_h
                    grid = Image.new("RGB", (total_w, total_h), bg)
                    grid.paste(fit_tile(images[0], big_w, total_h), (0, 0))
                    for i, img in enumerate(images[1:n]):
                        grid.paste(fit_tile(img, small_w, small_h), (big_w, i * small_h))

            else:
                # Calcola tile_w e tile_h dal TARGET_PX per n≠4
                # Per layout a N colonne: total_px = n_cols * tile_w * tile_w * photo_ratio * n_rows
                first_row_cols = layout[0][0]
                n_rows = len(layout)
                tile_w = int((TARGET_PX / (first_row_cols * n_rows * photo_ratio)) ** 0.5)
                tile_h = int(tile_w * photo_ratio)

                row_images = []
                idx = 0
                total_w = None
                for row_def in layout:
                    n_cols = row_def[0]
                    row_imgs = images[idx:idx + n_cols]
                    idx += n_cols

                    if total_w is None:
                        cell_w = tile_w
                        total_w = cell_w * n_cols
                    else:
                        cell_w = total_w // n_cols

                    cell_h = tile_h

                    tiles = [fit_tile(img, cell_w, cell_h) for img in row_imgs]
                    row_img = Image.new("RGB", (total_w, cell_h), (0, 0, 0))
                    for i, tile in enumerate(tiles):
                        row_img.paste(tile, (i * cell_w, 0))
                    row_images.append(row_img)

                total_h = sum(r.height for r in row_images)
                grid = Image.new("RGB", (total_w, total_h), (0, 0, 0))
                y = 0
                for row_img in row_images:
                    grid.paste(row_img, (0, y))
                    y += row_img.height

            out = io.BytesIO()
            grid.save(out, format="JPEG", quality=92)
            out.seek(0)

            bot.send_document(
                chat_id,
                out,
                visible_file_name=f"mosaic_{n}foto.jpg",
                caption=f"✅ Collage {grid_label} ({aspect_label}) — {n} foto"
            )
            logger.info(f"   ✅ Mosaic {grid_label} inviato a uid={uid}")
            mosaic_markup = types.InlineKeyboardMarkup()
            mosaic_markup.row(
                types.InlineKeyboardButton("🔁 Riprova stesso filtro", callback_data="post_retry"),
                types.InlineKeyboardButton("🔄 Cambia filtro", callback_data="post_newfilter")
            )
            mosaic_markup.row(
                types.InlineKeyboardButton("🆕 Nuova foto e nuovo filtro", callback_data="post_newboth")
            )
            bot.send_message(chat_id, "Cosa vuoi fare adesso?", reply_markup=mosaic_markup)
        except Exception as e:
            logger.error(f"   ❌ Errore assemblaggio mosaic: {e}", exc_info=True)
            bot.send_message(chat_id, f"❌ Errore nell'assemblaggio:\n<code>{html.escape(str(e))}</code>")

    executor.submit(build)

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Foto non autorizzata: uid={uid} username={m.from_user.username}")
        return
    username = m.from_user.username or m.from_user.first_name

    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img_data = bot.download_file(file_info.file_path)
        logger.info(f"🖼️ Foto da {username} (id={uid}), {len(img_data)} bytes")
    except Exception as e:
        logger.error(f"❌ Errore download foto da {username}: {e}")
        bot.reply_to(m, "❌ Errore nel scaricare la foto. Riprova.")
        return

    # ── MODALITÀ STEREO ───────────────────────────────────────────────────────
    if stereo_waiting.pop(uid, False):
        bot.send_message(m.chat.id,
            "🎥 <b>Elaborazione stereo avviata!</b>\n"
            "⏳ Attendi ~30 secondi.")
        executor.submit(_run_stereo, m.chat.id, uid, username, img_data)
        return

    # ── MODALITÀ MIRROR ───────────────────────────────────────────────────────
    if mirror_waiting.pop(uid, False):
        prompt = _build_mirror_prompt(img_data)
        mirror_last_img[uid] = img_data
        # Invia prompt in anteprima con pulsante conferma
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 Genera", callback_data="mirror_confirm"))
        markup.add(types.InlineKeyboardButton("❌ Annulla", callback_data="mirror_menu"))
        chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
        for idx, chunk in enumerate(chunks):
            header = "🪞 <b>Mirror Outfits — Prompt generato:</b>\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>",
                reply_markup=markup if idx == len(chunks)-1 else None)
        # Salva prompt per uso nel callback
        mirror_pending_prompt[uid] = prompt
        return

    # ── MODALITÀ MOSAIC ───────────────────────────────────────────────────────
    if uid in mosaic_collecting:
        session = mosaic_collecting[uid]
        if session.get('timer'):
            session['timer'].cancel()
        session['photos'].append(img_data)
        n = len(session['photos'])
        logger.info(f"   🖼️ Mosaic raccolta: {n} foto per uid={uid}")

        # Rileva aspect ratio dalla prima foto
        if n == 1:
            try:
                first_img = Image.open(io.BytesIO(img_data))
                w, h = first_img.size
                session['aspect'] = _detect_aspect_label(w, h)
                logger.info(f"   📐 Aspect rilevato: {session['aspect']} ({w}x{h})")
            except Exception:
                session['aspect'] = '?'

        aspect_label = session.get('aspect', '?')

        if n >= 9:
            # Massimo raggiunto — forza assemblaggio
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"✅ Procedi ({n} foto)",
                callback_data=f"mosaic_build_{uid}"
            ))
            bot.reply_to(m,
                f"📷 <b>{n} foto</b> — massimo raggiunto!\n"
                f"Formato: <b>{aspect_label}</b>",
                reply_markup=markup)
        elif n >= 2:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"✅ Procedi ({n} foto)",
                callback_data=f"mosaic_build_{uid}"
            ))
            bot.reply_to(m,
                f"📷 <b>{n} foto</b> ricevute — puoi procedere o inviarne altre (max 9).\n"
                f"Formato: <b>{aspect_label}</b>",
                reply_markup=markup)
        else:
            # n == 1
            bot.reply_to(m, f"📷 Prima foto ricevuta. Invia almeno un'altra per il collage.")

        # Timer 5 minuti safety net
        t = threading.Timer(300, _finalize_mosaic, args=[uid, m.chat.id])
        t.daemon = True
        t.start()
        session['timer'] = t
        return
    # ─────────────────────────────────────────────────────────────────────────

    fkey = user_filter[uid]
    pending[uid] = {'img': img_data, 'filter_key': fkey}
    last_img[uid] = img_data  # aggiorna subito — anche se la generazione fallisce, retry usa questa foto

    if not fkey:
        bot.reply_to(m, "📷 Foto ricevuta!\n\n🎨 <b>Scegli una categoria:</b>", reply_markup=cat_keyboard())
    else:
        fname = FILTERS[fkey]["label"]
        _send_confirmation(m.chat.id, uid, fname, reply_to=m.message_id)

FULLBODY_3X3_BASE = (
    "Using the uploaded photo as the identity and style reference, create a full body editorial grid "
    "with EXACTLY 3 columns and 3 rows — 9 panels total, square or landscape orientation. "
    "The grid MUST be 3 wide by 3 tall. Strictly 3x3, no other layout. "
    "IDENTITY LOCK: Preserve the exact person from the photo — same face, facial structure, skin tone, hair, "
    "outfit, shoes, accessories, jewelry, and any distinctive elements visible in the image. "
    "Replicate the outfit completely and consistently across every single panel. "
    "FRAMING: Each panel shows the FULL BODY from head to toe — outfit fully visible in every panel. "
    "Wide enough framing to include the complete silhouette, shoes included. "
    "SETTING: Use the same background environment and lighting mood from the reference photo. "
    "Natural realistic skin tones. Medium to high contrast. Thin gutters between panels. High panel consistency. "
    "85mm lens look. Cinematic editorial quality. "
    "9 full body poses (randomly selected, in this order): "
    "{poses} "
    "Ultra high resolution photorealistic editorial fashion contact sheet. "
)



def resolve_prompt(fkey):
    """Risolve il prompt del filtro. Se è callable (lambda), lo esegue e costruisce il testo finale."""
    raw = FILTERS[fkey]["prompt"]
    if fkey == "artistic_style":
        prompt, _ = build_artistic_style_prompt()
        return prompt
    if callable(raw):
        if fkey == "fullbody_3x3":
            poses = raw()
            pose_str = ", ".join(f"{i+1}-{p}" for i, p in enumerate(poses))
            return FULLBODY_3X3_BASE.format(poses=pose_str)
        return raw()
    return raw

# Salva lo stile estratto per mostrarlo nella preview
pending_artistic_style = {}  # uid → style label estratto

# --- HELPER: invia conferma con preview prompt ---
def _send_confirmation(chat_id, uid, fname, reply_to=None):
    fkey = user_filter[uid]

    # Per artistic_style: estrai stile casuale e salvalo
    if fkey == "artistic_style":
        prompt, style_label = build_artistic_style_prompt()
        pending_artistic_style[uid] = style_label
        filter_prompt = prompt
        fname_display = f"🎨 Stile Artistico — <b>{style_label.split(' — ')[0]}</b>"
    else:
        filter_prompt = resolve_prompt(fkey) if fkey else ""
        fname_display = fname

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🚀 CONFERMA", callback_data="confirm_fx"),
        types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_fx")
    )
    markup.add(types.InlineKeyboardButton("🔄 Cambia filtro", callback_data="back_cats"))

    # Preview prompt con chunking
    CHUNK = 3800
    header = f"🎨 Filtro: <b>{fname_display}</b>\n\n📝 <b>Prompt:</b>\n"
    full = filter_prompt

    if len(full) <= CHUNK:
        text = f"{header}<code>{html.escape(full)}</code>\n\nProcedere?"
        if reply_to:
            bot.send_message(chat_id, text, reply_to_message_id=reply_to, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    else:
        chunks = [full[i:i+CHUNK] for i in range(0, len(full), CHUNK)]
        for idx, chunk in enumerate(chunks):
            prefix = header if idx == 0 else f"<i>({idx+1}/{len(chunks)})</i>\n"
            bot.send_message(chat_id, f"{prefix}<code>{html.escape(chunk)}</code>", parse_mode="HTML",
                             **({"reply_to_message_id": reply_to} if reply_to and idx == 0 else {}))
        bot.send_message(chat_id,
            f"📋 Prompt completo ({len(chunks)} parti). Procedere?",
            reply_markup=markup, parse_mode="HTML")

# --- GENERAZIONE ---
def _run_generation(chat_id, uid, username, data):
    fkey = data['filter_key']
    # Per artistic_style: usa il prompt già estratto in _send_confirmation
    if fkey == "artistic_style" and uid in pending_artistic_style:
        style_label = pending_artistic_style.pop(uid)
        key = next((k for k in ARTISTIC_STYLE_PROMPTS if k in style_label), None)
        filter_prompt = ARTISTIC_STYLE_PROMPTS[key] if key else ARTISTIC_STYLE_PROMPTS["🌂 Magritte"]
        fname = f"🎨 {style_label.split(' — ')[0]}"
    else:
        filter_prompt = resolve_prompt(fkey)
        fname = FILTERS[fkey]["label"]
    img_bytes = data['img']

    t_start = time.time()
    logger.info(f"   🎨 Inizio generazione | {username} | filtro: {fkey}")

    # Wrapper editoriale per ridurre falsi positivi IMAGE_SAFETY
    EDITORIAL_WRAPPER = (
        "This is a professional editorial post-production request for a high-fashion photography project. "
        "Apply the following artistic filter to the provided image, maintaining the subject's identity, "
        "pose and composition. This is a legitimate creative and commercial photography workflow. "
        "Filter to apply: "
    )

    try:
        full_prompt = EDITORIAL_WRAPPER + filter_prompt
        last_prompt[uid] = full_prompt

        elapsed = round(time.time() - t_start, 1)

        # Invia prompt Flow-ready
        post_markup = types.InlineKeyboardMarkup()
        post_markup.row(
            types.InlineKeyboardButton("🎨 Nuovo filtro, stessa foto", callback_data="post_newfilter"),
            types.InlineKeyboardButton("🔁 Stesso filtro, nuova foto", callback_data="post_newphoto")
        )
        post_markup.row(
            types.InlineKeyboardButton("🆕 Nuova foto e nuovo filtro", callback_data="post_newboth")
        )

        bot.send_message(chat_id, f"⚡ <b>Prompt pronto.</b> Usa Flow per generare l'immagine.")
        chunks = [full_prompt[i:i+3800] for i in range(0, len(full_prompt), 3800)]
        for idx, chunk in enumerate(chunks):
            header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
            if idx == len(chunks) - 1:
                bot.send_message(chat_id, f"{header}<code>{html.escape(chunk)}</code>",
                    reply_markup=post_markup)
            else:
                bot.send_message(chat_id, f"{header}<code>{html.escape(chunk)}</code>")

        # Caption con from_filter
        cap_result, _ = caption.from_filter(data['img'], fname)
        if cap_result:
            bot.send_message(chat_id, cap_result)

        logger.info(f"   ✅ Prompt inviato a {username} in {elapsed}s")
        return

    except Exception as e:
        elapsed = round(time.time() - t_start, 1)
        logger.error(f"   ❌ Errore generazione prompt ({elapsed}s): {e}", exc_info=True)
        bot.send_message(chat_id, f"❌ Errore interno:\n<code>{html.escape(str(e))}</code>")

# --- MAIN ---
if __name__ == "__main__":
    logger.info(f"🎨 Avvio Filtro v{VERSION}")
    server.start()
    bot.infinity_polling()
