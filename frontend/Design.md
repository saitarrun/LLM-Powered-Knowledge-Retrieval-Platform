# Design System Specification



## 1. Overview & Creative North Star: "Cinematic Intelligence"

This design system is anchored in the concept of **Cinematic Intelligence**. It moves away from the sterile, flat world of traditional SaaS interfaces toward a high-fidelity, atmospheric experience. We are not just building layouts; we are crafting a digital environment that feels "alive."



The Creative North Star focuses on **Fluidity and Depth**. By utilizing deep charcoal foundations and piercing neon accents, we create a high-contrast editorial look. The "template" feel is broken through the use of intentional asymmetry—overlapping elements, floating glass containers, and typography that breathes with massive scale shifts. It is a fusion of futuristic tech and premium automotive aesthetics.



---



## 2. Colors & Surface Philosophy

The palette is a sophisticated interplay of absolute blacks and glowing reds. The goal is to make the interface feel like a premium, dark-mode cockpit.



### Color Tokens (Material Design Core)

* **Primary (The Glow):** `#ff8e7d` (Surface) | `#eb0000` (Primary Dim) | `#650000` (On Primary)

* **Background (The Void):** `#0e0e0e` (Base) | `#000000` (Surface Container Lowest)

* **Surfaces (The Layers):**

* `surface_container_low`: `#131313`

* `surface_container_high`: `#201f1f`

* `surface_variant`: `#262626`



### The "No-Line" Rule

**Explicit Instruction:** Do not use 1px solid borders to define section boundaries. This is the hallmark of "cheap" UI. Instead, separate content through:

1. **Tonal Shifts:** Place a `surface_container_high` card against a `background` base.

2. **Vertical Space:** Use our generous spacing scale (`16` or `20`) to separate sections.

3. **Soft Glows:** Use the `primary_dim` as a localized, blurred background glow to highlight an area.



### Surface Hierarchy & Nesting

Treat the UI as physical layers. Use `surface_container_lowest` for the deepest elements and `surface_bright` for floating, active components. This "nested" depth mimics fine paper or layered smoked glass.



### The "Glass & Gradient" Rule

Floating elements (Modals, Dropdowns, Feature Cards) must use **Glassmorphism**:

* **Fill:** `secondary_container` at 40%–60% opacity.

* **Backdrop Blur:** Minimum 20px–40px.

* **Gradient Polish:** Apply a subtle linear gradient from `primary` to `primary_container` (at 10% opacity) across the surface to give it a "soulful" shimmer.



---



## 3. Typography: Editorial High-Contrast

We use **Plus Jakarta Sans** as our sole typeface, relying on extreme scale and weight contrast to drive the narrative.



* **Display (The Statement):** `display-lg` (3.5rem). Use for hero sections with tight letter-spacing (-0.02em).

* **Headline (The Guide):** `headline-lg` (2rem). Bold, authoritative, always `on_surface` (pure white).

* **Body (The Content):** `body-md` (0.875rem). Use `on_surface_variant` (soft gray) for body copy to ensure the headlines pop.

* **Label (The Utility):** `label-sm` (0.6875rem). All-caps with generous letter-spacing (0.05em) for a high-tech, tactical feel.



**Brand Identity Tip:** Use "inline" primary color highlights. In a white headline, wrap a key word in `primary_dim` to draw the eye immediately.



---



## 4. Elevation & Depth: Tonal Layering

Traditional drop shadows are forbidden unless specified. We achieve "lift" through light, not shadow.



* **The Layering Principle:** Stack your surfaces. A card should be `surface_container_highest` sitting on a `surface_container_low` section. The contrast is the border.

* **Ambient Shadows:** When a float is required, use a blur of 60px–100px with a 4% opacity of `#ff0000` (red tint) rather than black. This simulates the "Neon Glow" reflecting off the dark surface.

* **The "Ghost Border" Fallback:** If accessibility requires a border, use `outline_variant` at 15% opacity. It should be felt, not seen.

* **Glassmorphism Depth:** The backdrop blur is the primary tool for depth. It creates a sense of "frosted intelligence," where the background colors bleed through the active container.



---



## 5. Components



### Buttons

* **Primary:** High-saturation `primary` fill with `on_primary` text. No border. Large `xl` (1.5rem) or `full` (9999px) roundedness.

* **Secondary:** Glassmorphic fill (`surface_variant` at 30%) with a "Ghost Border."

* **Tertiary:** Pure text using `primary_fixed` with a hover state that triggers a subtle `primary` underline.



### Input Fields

* **Style:** `surface_container_low` fill. No visible border in resting state.

* **Active State:** A 1px "Ghost Border" using `primary_dim` at 40% and a subtle red outer glow.



### Cards & Lists

* **Forbid Dividers:** Do not use lines to separate list items. Use a `3` (1rem) spacing gap or a slight shift in background color (`surface_container_low` to `surface_container_high`).

* **Fluid Motion:** Cards should have a `lg` (1rem) corner radius. On hover, the background should transition slightly toward `surface_bright`.



### Additional Component: "The Glow Chip"

A specialized tag for status or categories. Use a semi-transparent `primary_container` background with a `primary` dot (4px) to the left of the text. It should look like a live sensor light.



---



## 6. Do's and Don'ts



### Do:

* **Do** use massive amounts of negative space. If in doubt, add more.

* **Do** use overlapping elements (e.g., an image bleeding out of a glass container) to break the grid.

* **Do** ensure text is always `on_surface` (White/Light Gray) against the dark background for AAA accessibility.

* **Do** use `primary` sparingly as a "laser pointer" to direct user attention.



### Don't:

* **Don't** use pure blue or "standard" corporate colors. Stick to the Red/Black/Charcoal spectrum.

* **Don't** use 1px solid white or gray borders. They kill the cinematic atmosphere.

* **Don't** use traditional "Material" drop shadows. Stick to tonal layering and blurred neon glows.

* **Don't** clutter the UI. This system is editorial; let the visuals speak.



---



## 7. Design & UX Glossary

### Visual Design Fundamentals
* **Typography**: The styling and arrangement of text.
* **Typeface / Font Family**: A group of fonts with the same design style (e.g., Plus Jakarta Sans).
* **Font Weight**: How bold or light the text is.
* **Hierarchy**: Using size, weight, spacing, and color to show importance.
* **Color Palette**: The set of colors used in the interface.
* **Primary Color**: The main brand or action color (`#eb0000`).
* **Secondary Color**: A supporting color used less frequently.
* **Accent Color**: A highlight color used to draw attention.
* **Contrast**: The visual difference between elements (critical for readability).
* **Alignment**: Placing elements so they line up cleanly.
* **Spacing**: The gaps between elements. Good spacing improves clarity and polish.
* **Balance**: Visual distribution so the layout does not feel crowded.
* **Emphasis**: Making one element stand out more than others.
* **Scale**: Using size to create importance or structure.
* **Shadow / Elevation**: Visual depth (achieved here via tonal shifts and red glows).
* **Border Radius**: How rounded the corners are (e.g., `1rem` or `full`).
* **Iconography**: The system of icons used (e.g., Lucide React).

### Branding & Style
* **Brand Identity**: The visual and emotional personality of the brand.
* **Style Guide**: This document, defining colors, fonts, and rules.
* **Theme**: A consistent style (e.g., "Cinematic Intelligence" Dark Theme).
* **Design Language**: Broader visual and interaction rules.

### Design Systems
* **Design System**: Reusable components, patterns, and guidelines.
* **Component Library**: Collection of reusable UI parts (Buttons, Cards, etc.).
* **Pattern Library**: Repeatable solutions for common problems.
* **Design Token**: Named values (colors, spacing) used in code.
* **Variant**: Different versions of a component (Primary vs. Secondary button).

### Research & Testing
* **User Research**: Learning about users through interviews and testing.
* **Persona**: Fictional profile representing a target user.
* **Empathy Map**: Framework to understand user thoughts/feelings.
* **Usability Testing**: Finding confusion by watching users perform tasks.
* **A/B Testing**: Comparing two versions to see which performs better.
* **Heatmap**: Visual report showing user focus/clicks.
* **Card Sorting**: Understanding how users group information.
* **Tree Testing**: Testing navigation findability.

### Accessibility (a11y)
* **WCAG**: Web Content Accessibility Guidelines.
* **Screen Reader**: Tool that reads content aloud for visually impaired users.
* **Keyboard Navigation**: Navigating using only a keyboard.
* **Alt Text**: Image descriptions for assistive tools.
* **ARIA Labels**: Markup to help assistive tech understand elements.
* **Color Contrast Ratio**: Measurement of text readability against background.