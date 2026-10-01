// Every business fact on the site lives here, so details can be corrected in one place.
// Sources: the school's YouTube channel (incl. the "Building a Balanced Generation" video),
// and its public Facebook / Instagram bios and admission posts.

export const school = {
  name: "AIMS Grammar High School",
  shortName: "AIMS Grammar",
  sloganEn: "Small steps, big flight.",
  sloganUr: "ننھے قدم، بڑی اُڑان",
  sloganRoman: "Nanhay Qadam, Bari Urhan",
  promise: ["Happy", "Confident", "Competent"] as const,
  taglines: ["Learn", "Grow", "Succeed"] as const,
  session: "2026–27",
  admissionClasses: "Play Group to Pre-Nine",
  classesRun: "Play Group to Matric",

  address: {
    line1: "Darogha Abadi, Jinnah Road",
    line2: "Khiali, Gujranwala",
    region: "Punjab, Pakistan",
    // Opens the location in Google Maps (works on iPhone and Android).
    mapsUrl:
      "https://www.google.com/maps/search/?api=1&query=AIMS+Grammar+High+School+Jinnah+Road+Khiali+Gujranwala",
    embedUrl:
      "https://www.google.com/maps?q=AIMS+Grammar+High+School,+Jinnah+Road,+Khiali,+Gujranwala&output=embed",
  },

  phones: [
    { label: "055-4254102", href: "tel:+92554254102" },
    { label: "055-4440102", href: "tel:+92554440102" },
    { label: "0301-8640524", href: "tel:+923018640524" },
  ],
  // CONFIRM: assumed to be on WhatsApp. It's the mobile number listed on the school's Facebook page.
  whatsapp: { label: "0301-8640524", number: "923018640524" },
  // CONFIRM: the Facebook bio reads "aimshs@yaoo.com", which looks like a typo for yahoo.com.
  email: "aimshs@yahoo.com",

  social: {
    youtube: "https://youtube.com/@aimsgrammarhighschool?si=qvi08fYoxcNFoMRu",
    instagram: "https://www.instagram.com/aims_grammar_high_school?stkn=MTFoemw2cTBvZDltaQ==ki",
    facebook: "https://www.facebook.com/share/19NeFMLuxR/",
  },

  videos: {
    feature: { id: "SaFLlilsIMQ", title: "Building a Balanced Generation | Nanhay Qadam Bari Urhan" },
    toppers: "https://www.youtube.com/shorts/6qeDlIIKLFI",
  },
} as const;

export const whatsappLink = (text: string) =>
  `https://wa.me/${school.whatsapp.number}?text=${encodeURIComponent(text)}`;

export const nav = [
  { id: "vision", label: "Our vision" },
  { id: "journey", label: "Classes" },
  { id: "values", label: "Character" },
  { id: "life", label: "School life" },
  { id: "visit", label: "Contact" },
] as const;
