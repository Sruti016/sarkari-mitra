// ─── STATIC DATA — swap API calls when backend is ready ─────────────────────

// ── Languages ─────────────────────────────────────────────────────────────────
export const LANGUAGES = [
  { code: "hi",  label: "हिंदी"   },
  { code: "en",  label: "English" },
  { code: "mix", label: "Hinglish"},
];

// ── Translation helper ────────────────────────────────────────────────────────
export function t(lang, hi, en, mix) {
  if (lang === "hi")  return hi;
  if (lang === "en")  return en;
  return mix || hi;
}

// ── Quick actions (home screen) ───────────────────────────────────────────────
export const QUICK_ACTIONS = [
  {
    id: "eligibility",
    icon: "✅",
    hi:  "पात्रता जांचें",
    en:  "Check Eligibility",
    mix: "Eligibility Check",
    query: "Mujhe konsi scheme milegi?",
    color: "#16a34a",
    bg:    "#dcfce7",
  },
  {
    id: "documents",
    icon: "📄",
    hi:  "जरूरी दस्तावेज",
    en:  "Documents Needed",
    mix: "Documents Chahiye",
    query: "Scheme ke liye kaunse documents chahiye?",
    color: "#2563eb",
    bg:    "#dbeafe",
  },
  {
    id: "apply",
    icon: "📝",
    hi:  "आवेदन करें",
    en:  "How to Apply",
    mix: "Apply Kaise Karein",
    query: "Scheme ke liye apply kaise karein?",
    color: "#d97706",
    bg:    "#fef3c7",
  },
  {
    id: "schemes",
    icon: "🏛️",
    hi:  "सभी योजनाएं",
    en:  "All Schemes",
    mix: "Sab Schemes",
    query: "Sabhi government schemes batao.",
    color: "#7c3aed",
    bg:    "#ede9fe",
  },
];

// ── Popular schemes (pills + detail pages) ────────────────────────────────────
export const POPULAR_SCHEMES = [
  { id: "pm-kisan",   icon: "🌾", hi: "PM किसान",      en: "PM Kisan",      query: "PM Kisan Samman Nidhi ke baare mein batao" },
  { id: "ayushman",   icon: "🏥", hi: "आयुष्मान",      en: "Ayushman",      query: "Ayushman Bharat scheme kya hai?" },
  { id: "pm-awas",    icon: "🏠", hi: "PM आवास",        en: "PM Awas",       query: "PM Awas Yojana ke baare mein batao" },
  { id: "fasal-bima", icon: "🌱", hi: "फसल बीमा",      en: "Fasal Bima",    query: "Pradhan Mantri Fasal Bima Yojana batao" },
  { id: "kcc",        icon: "💳", hi: "किसान क्रेडिट", en: "Kisan Credit",  query: "Kisan Credit Card kya hai?" },
  { id: "ujjwala",    icon: "🔥", hi: "उज्ज्वला",       en: "Ujjwala",       query: "PM Ujjwala Yojana ke baare mein batao" },
  { id: "sukanya",    icon: "👧", hi: "सुकन्या",         en: "Sukanya",       query: "Sukanya Samriddhi Yojana ke baare mein batao" },
  { id: "shram-yogi", icon: "👷", hi: "श्रम योगी",      en: "Shram Yogi",    query: "PM Shram Yogi Mandhan kya hai?" },
];

// ── Full yojana detail data ───────────────────────────────────────────────────
export const YOJANA_DETAILS = {
  "pm-kisan": {
    id: "pm-kisan",
    icon: "🌾",
    name: "PM Kisan Samman Nidhi",
    nameHi: "पीएम किसान सम्मान निधि",
    ministry: "कृषि मंत्रालय",
    ministryEn: "Ministry of Agriculture",
    benefit: "₹6,000/साल",
    benefitEn: "₹6,000/year",
    benefitDesc: "3 किश्तों में — हर 4 महीने ₹2,000 सीधे बैंक में",
    benefitDescEn: "3 installments — ₹2,000 every 4 months directly to bank",
    color: "#16a34a",
    bg: "#dcfce7",
    link: "pmkisan.gov.in",
    helpline: "155261",
    eligibility: [
      { hi: "छोटे और सीमांत किसान", en: "Small & marginal farmers" },
      { hi: "2 हेक्टेयर तक जमीन", en: "Land up to 2 hectares" },
      { hi: "आधार से लिंक बैंक खाता", en: "Aadhaar-linked bank account" },
      { hi: "वार्षिक आय ₹2 लाख से कम", en: "Annual income below ₹2 lakh" },
    ],
    documents: [
      { hi: "आधार कार्ड", en: "Aadhaar Card" },
      { hi: "जमीन के कागज (खसरा/खतौनी)", en: "Land records (Khasra/Khatauni)" },
      { hi: "बैंक पासबुक", en: "Bank Passbook" },
      { hi: "मोबाइल नंबर", en: "Mobile Number" },
    ],
    steps: [
      { hi: "pmkisan.gov.in वेबसाइट खोलें", en: "Open pmkisan.gov.in website" },
      { hi: '"New Farmer Registration" पर click करें', en: 'Click "New Farmer Registration"' },
      { hi: "आधार नंबर और मोबाइल डालें", en: "Enter Aadhaar number and mobile" },
      { hi: "जमीन की जानकारी भरें", en: "Fill land details" },
      { hi: "दस्तावेज़ upload करें और submit करें", en: "Upload documents and submit" },
    ],
  },
  "ayushman": {
    id: "ayushman",
    icon: "🏥",
    name: "Ayushman Bharat PM-JAY",
    nameHi: "आयुष्मान भारत PM-JAY",
    ministry: "स्वास्थ्य मंत्रालय",
    ministryEn: "Ministry of Health",
    benefit: "₹5 लाख/साल",
    benefitEn: "₹5 Lakh/year",
    benefitDesc: "मुफ़्त इलाज — 25,000+ अस्पतालों में",
    benefitDescEn: "Free treatment — in 25,000+ hospitals",
    color: "#0891b2",
    bg: "#cffafe",
    link: "pmjay.gov.in",
    helpline: "14555",
    eligibility: [
      { hi: "SECC 2011 सूची में नाम", en: "Name in SECC 2011 list" },
      { hi: "BPL / गरीब परिवार", en: "BPL / Below Poverty Line family" },
      { hi: "सालाना आय ₹2.5 लाख से कम", en: "Annual income below ₹2.5 lakh" },
      { hi: "राशन कार्ड धारक", en: "Ration card holder" },
    ],
    documents: [
      { hi: "आधार कार्ड", en: "Aadhaar Card" },
      { hi: "राशन कार्ड", en: "Ration Card" },
      { hi: "मोबाइल नंबर", en: "Mobile Number" },
    ],
    steps: [
      { hi: "pmjay.gov.in खोलें", en: "Open pmjay.gov.in" },
      { hi: '"Am I Eligible" पर click करें', en: 'Click "Am I Eligible"' },
      { hi: "Mobile नंबर या Ration Card डालें", en: "Enter mobile or Ration Card number" },
      { hi: "अपना नाम list में देखें", en: "Check your name in the list" },
      { hi: "नज़दीकी CSC/अस्पताल से card बनवाएं", en: "Get card from nearest CSC/hospital" },
    ],
  },
  "pm-awas": {
    id: "pm-awas",
    icon: "🏠",
    name: "PM Awas Yojana",
    nameHi: "प्रधानमंत्री आवास योजना",
    ministry: "आवास मंत्रालय",
    ministryEn: "Ministry of Housing",
    benefit: "₹2.67 लाख सब्सिडी",
    benefitEn: "₹2.67L subsidy",
    benefitDesc: "Home loan पर ब्याज में छूट",
    benefitDescEn: "Interest subsidy on home loan",
    color: "#ea580c",
    bg: "#ffedd5",
    link: "pmaymis.gov.in",
    helpline: "1800-11-6163",
    eligibility: [
      { hi: "पहली बार घर खरीद रहे हैं", en: "First-time home buyer" },
      { hi: "पहले से पक्का घर नहीं है", en: "No pucca house already" },
      { hi: "EWS: आय ₹3 लाख से कम", en: "EWS: Income below ₹3 lakh" },
      { hi: "LIG: आय ₹3-6 लाख के बीच", en: "LIG: Income ₹3-6 lakh" },
    ],
    documents: [
      { hi: "आधार कार्ड", en: "Aadhaar Card" },
      { hi: "आय प्रमाण पत्र", en: "Income Certificate" },
      { hi: "बैंक खाता विवरण", en: "Bank Account Statement" },
      { hi: "संपत्ति के दस्तावेज़", en: "Property Documents" },
    ],
    steps: [
      { hi: "pmaymis.gov.in खोलें", en: "Open pmaymis.gov.in" },
      { hi: '"Citizen Assessment" पर click करें', en: 'Click "Citizen Assessment"' },
      { hi: "आधार नंबर से verify करें", en: "Verify with Aadhaar number" },
      { hi: "फॉर्म भरें — आय, संपत्ति की जानकारी", en: "Fill form — income, property details" },
      { hi: "Bank में जाकर subsidy के लिए apply करें", en: "Visit bank to apply for subsidy" },
    ],
  },
  "fasal-bima": {
    id: "fasal-bima",
    icon: "🌱",
    name: "PM Fasal Bima Yojana",
    nameHi: "प्रधानमंत्री फसल बीमा योजना",
    ministry: "कृषि मंत्रालय",
    ministryEn: "Ministry of Agriculture",
    benefit: "फसल नुकसान पर मुआवज़ा",
    benefitEn: "Compensation for crop loss",
    benefitDesc: "बाढ़, सूखा, ओले — सब covered",
    benefitDescEn: "Flood, drought, hail — all covered",
    color: "#16a34a",
    bg: "#dcfce7",
    link: "pmfby.gov.in",
    helpline: "14447",
    eligibility: [
      { hi: "सभी किसान पात्र हैं", en: "All farmers are eligible" },
      { hi: "Kharif और Rabi दोनों फसलें", en: "Both Kharif and Rabi crops" },
      { hi: "KCC loan वाले किसानों के लिए अनिवार्य", en: "Mandatory for KCC loan farmers" },
    ],
    documents: [
      { hi: "आधार कार्ड", en: "Aadhaar Card" },
      { hi: "जमीन के कागज", en: "Land records" },
      { hi: "बैंक पासबुक", en: "Bank Passbook" },
      { hi: "बुवाई प्रमाण पत्र", en: "Sowing Certificate" },
    ],
    steps: [
      { hi: "pmfby.gov.in खोलें या CSC जाएं", en: "Open pmfby.gov.in or visit CSC" },
      { hi: "बुवाई के 2 हफ्ते के अंदर apply करें", en: "Apply within 2 weeks of sowing" },
      { hi: "फसल और जमीन की जानकारी भरें", en: "Fill crop and land details" },
      { hi: "प्रीमियम भरें (बहुत कम होती है)", en: "Pay premium (very low amount)" },
      { hi: "नुकसान होने पर 72 घंटे में claim करें", en: "Claim within 72 hours of damage" },
    ],
  },
  "kcc": {
    id: "kcc",
    icon: "💳",
    name: "Kisan Credit Card",
    nameHi: "किसान क्रेडिट कार्ड",
    ministry: "वित्त मंत्रालय",
    ministryEn: "Ministry of Finance",
    benefit: "₹3 लाख तक loan",
    benefitEn: "Loan up to ₹3 lakh",
    benefitDesc: "सिर्फ 4% ब्याज पर खेती के लिए loan",
    benefitDescEn: "Only 4% interest loan for farming",
    color: "#7c3aed",
    bg: "#ede9fe",
    link: "kcc.gov.in",
    helpline: "1800-180-1551",
    eligibility: [
      { hi: "सभी किसान पात्र हैं", en: "All farmers eligible" },
      { hi: "मछुआरे और पशुपालक भी", en: "Also fishermen and animal rearers" },
      { hi: "18 से 75 साल की आयु", en: "Age 18 to 75 years" },
    ],
    documents: [
      { hi: "आधार कार्ड", en: "Aadhaar Card" },
      { hi: "जमीन के कागज", en: "Land records" },
      { hi: "पासपोर्ट साइज फोटो", en: "Passport size photo" },
      { hi: "बैंक खाता", en: "Bank account" },
    ],
    steps: [
      { hi: "नज़दीकी Bank/CSC जाएं", en: "Visit nearest Bank/CSC" },
      { hi: "KCC application form लें", en: "Get KCC application form" },
      { hi: "दस्तावेज़ के साथ जमा करें", en: "Submit with documents" },
      { hi: "Bank verification करेगी", en: "Bank will verify" },
      { hi: "Card 15 दिनों में मिल जाएगा", en: "Card received in 15 days" },
    ],
  },
  "ujjwala": {
    id: "ujjwala",
    icon: "🔥",
    name: "PM Ujjwala Yojana",
    nameHi: "प्रधानमंत्री उज्ज्वला योजना",
    ministry: "पेट्रोलियम मंत्रालय",
    ministryEn: "Ministry of Petroleum",
    benefit: "मुफ़्त LPG Connection",
    benefitEn: "Free LPG Connection",
    benefitDesc: "गरीब परिवारों को मुफ़्त गैस कनेक्शन",
    benefitDescEn: "Free gas connection for poor families",
    color: "#dc2626",
    bg: "#fee2e2",
    link: "pmuy.gov.in",
    helpline: "1906",
    eligibility: [
      { hi: "BPL परिवार की महिलाएं", en: "Women from BPL families" },
      { hi: "SC/ST परिवार", en: "SC/ST families" },
      { hi: "घर में पहले से LPG नहीं", en: "No existing LPG connection at home" },
      { hi: "18 साल से ऊपर की महिला", en: "Woman above 18 years" },
    ],
    documents: [
      { hi: "BPL राशन कार्ड", en: "BPL Ration Card" },
      { hi: "आधार कार्ड", en: "Aadhaar Card" },
      { hi: "बैंक खाता", en: "Bank Account" },
      { hi: "पासपोर्ट साइज फोटो", en: "Passport size photo" },
    ],
    steps: [
      { hi: "नज़दीकी LPG distributor जाएं", en: "Visit nearest LPG distributor" },
      { hi: "Form-1 और Form-2 लें", en: "Get Form-1 and Form-2" },
      { hi: "दस्तावेज़ जमा करें", en: "Submit documents" },
      { hi: "Verification के बाद connection मिलेगा", en: "Connection after verification" },
    ],
  },
  "sukanya": {
    id: "sukanya",
    icon: "👧",
    name: "Sukanya Samriddhi Yojana",
    nameHi: "सुकन्या समृद्धि योजना",
    ministry: "वित्त मंत्रालय",
    ministryEn: "Ministry of Finance",
    benefit: "8.2% ब्याज दर",
    benefitEn: "8.2% Interest Rate",
    benefitDesc: "बेटी की पढ़ाई और शादी के लिए बचत",
    benefitDescEn: "Savings for daughter's education & marriage",
    color: "#db2777",
    bg: "#fce7f3",
    link: "nsiindia.gov.in",
    helpline: "1800-266-6868",
    eligibility: [
      { hi: "10 साल से कम उम्र की बेटी", en: "Daughter below 10 years" },
      { hi: "एक परिवार में 2 बेटियों तक", en: "Up to 2 daughters per family" },
    ],
    documents: [
      { hi: "बेटी का जन्म प्रमाण पत्र", en: "Daughter's birth certificate" },
      { hi: "माता/पिता का आधार कार्ड", en: "Parent's Aadhaar Card" },
      { hi: "पासपोर्ट साइज फोटो", en: "Passport size photo" },
    ],
    steps: [
      { hi: "नज़दीकी Post Office या Bank जाएं", en: "Visit nearest Post Office or Bank" },
      { hi: "SSY account opening form लें", en: "Get SSY account opening form" },
      { hi: "दस्तावेज़ के साथ जमा करें", en: "Submit with documents" },
      { hi: "₹250 minimum deposit से खाता खुलेगा", en: "Account opens with minimum ₹250 deposit" },
    ],
  },
  "shram-yogi": {
    id: "shram-yogi",
    icon: "👷",
    name: "PM Shram Yogi Mandhan",
    nameHi: "PM श्रम योगी मानधन",
    ministry: "श्रम मंत्रालय",
    ministryEn: "Ministry of Labour",
    benefit: "₹3,000/माह पेंशन",
    benefitEn: "₹3,000/month pension",
    benefitDesc: "60 साल के बाद हर महीने पेंशन",
    benefitDescEn: "Monthly pension after 60 years",
    color: "#0369a1",
    bg: "#e0f2fe",
    link: "maandhan.in",
    helpline: "14434",
    eligibility: [
      { hi: "असंगठित क्षेत्र के मज़दूर", en: "Unorganized sector workers" },
      { hi: "18-40 साल की आयु", en: "Age 18-40 years" },
      { hi: "मासिक आय ₹15,000 से कम", en: "Monthly income below ₹15,000" },
      { hi: "EPFO/ESIC में registered नहीं", en: "Not registered under EPFO/ESIC" },
    ],
    documents: [
      { hi: "आधार कार्ड", en: "Aadhaar Card" },
      { hi: "बैंक पासबुक", en: "Bank Passbook" },
      { hi: "मोबाइल नंबर", en: "Mobile Number" },
    ],
    steps: [
      { hi: "नज़दीकी CSC centre जाएं", en: "Visit nearest CSC centre" },
      { hi: "आधार और बैंक details दें", en: "Provide Aadhaar and bank details" },
      { hi: "योगदान राशि चुनें", en: "Choose contribution amount" },
      { hi: "Auto-debit setup करें", en: "Set up auto-debit" },
    ],
  },
};

// ── Scheme cards (for /schemes page) ─────────────────────────────────────────
export const SCHEME_CARDS = [
  {
    id: 1,
    yojanaId: "pm-kisan",
    name: "PM Kisan Samman Nidhi",
    icon: "🌾",
    benefit: "₹6,000/साल",
    benefitEn: "₹6,000/year",
    eligible: "yes",
    reasonHi: "छोटे किसान — पात्र हैं",
    reasonEn: "Small farmer — Eligible",
    ministry: "कृषि",
    link: "pmkisan.gov.in",
    category: "farmer",
  },
  {
    id: 2,
    yojanaId: "fasal-bima",
    name: "Fasal Bima Yojana",
    icon: "🌱",
    benefit: "फसल बीमा",
    benefitEn: "Crop Insurance",
    eligible: "yes",
    reasonHi: "किसान प्रोफ़ाइल मेल खाता है",
    reasonEn: "Farmer profile matches",
    ministry: "कृषि",
    link: "pmfby.gov.in",
    category: "farmer",
  },
  {
    id: 3,
    yojanaId: "pm-awas",
    name: "PM Awas Yojana",
    icon: "🏠",
    benefit: "₹2.67 लाख सब्सिडी",
    benefitEn: "₹2.67L subsidy",
    eligible: "maybe",
    reasonHi: "दस्तावेज़ सत्यापन आवश्यक",
    reasonEn: "Documents verification needed",
    ministry: "आवास",
    link: "pmaymis.gov.in",
    category: "housing",
  },
  {
    id: 4,
    yojanaId: "ayushman",
    name: "Ayushman Bharat",
    icon: "🏥",
    benefit: "₹5 लाख स्वास्थ्य बीमा",
    benefitEn: "₹5L health cover",
    eligible: "no",
    reasonHi: "आय सीमा से अधिक",
    reasonEn: "Income above threshold",
    ministry: "स्वास्थ्य",
    link: "pmjay.gov.in",
    category: "health",
  },
  {
    id: 5,
    yojanaId: "kcc",
    name: "Kisan Credit Card",
    icon: "💳",
    benefit: "₹3 लाख loan",
    benefitEn: "₹3L loan",
    eligible: "yes",
    reasonHi: "किसान — पात्र हैं",
    reasonEn: "Farmer — Eligible",
    ministry: "वित्त",
    link: "kcc.gov.in",
    category: "farmer",
  },
  {
    id: 6,
    yojanaId: "ujjwala",
    name: "PM Ujjwala Yojana",
    icon: "🔥",
    benefit: "मुफ़्त LPG",
    benefitEn: "Free LPG",
    eligible: "maybe",
    reasonHi: "BPL status verify करें",
    reasonEn: "Verify BPL status",
    ministry: "पेट्रोलियम",
    link: "pmuy.gov.in",
    category: "other",
  },
];

// ── Bot responses ─────────────────────────────────────────────────────────────
export const BOT_RESPONSES = {
  "pm kisan": {
    text: `🌾 **पीएम किसान सम्मान निधि**\n\nसरकार हर साल **₹6,000** सीधे आपके बैंक खाते में देती है!\n\n**3 किश्तों में मिलता है:**\n• हर 4 महीने में ₹2,000\n• सीधे बैंक खाते में (DBT)\n\n**कौन पा सकता है?**\n• छोटे किसान (2 हेक्टेयर तक जमीन)\n• आधार लिंक्ड बैंक खाता\n\n**कहाँ करें आवेदन?**\n📱 pmkisan.gov.in\n📞 हेल्पलाइन: 155261`,
    sources: ["pm_kisan.pdf"],
    profile: { profession: "किसान" },
  },
  ayushman: {
    text: `🏥 **आयुष्मान भारत – PM-JAY**\n\nगरीब परिवारों को **मुफ़्त इलाज** मिलता है!\n\n**क्या मिलता है?**\n• ₹5 लाख का मुफ़्त इलाज हर साल\n• 25,000+ सरकारी-प्राइवेट अस्पताल\n• कोई प्रीमियम नहीं – **बिल्कुल मुफ़्त!**\n\n**पात्रता जांचें:**\n📱 pmjay.gov.in → "Am I Eligible"\n📞 हेल्पलाइन: 14555 (मुफ़्त)`,
    sources: ["ayushman.pdf"],
    profile: {},
  },
  awas: {
    text: `🏠 **प्रधानमंत्री आवास योजना**\n\nसबके लिए पक्का घर – सरकार का सपना!\n\n**कितनी सब्सिडी मिलती है?**\n• EWS/LIG: ₹2.67 लाख तक\n• MIG-I: ₹2.35 लाख तक\n\n**कौन आवेदन कर सकता है?**\n• पहली बार घर खरीद रहे हैं\n• पहले से पक्का घर नहीं है\n\n📱 pmaymis.gov.in\n📞 1800-11-6163 (मुफ़्त)`,
    sources: ["pm_awas.pdf"],
    profile: {},
  },
  eligibility: {
    text: `✅ **पात्रता जाँचने के लिए बताएं:**\n\n• 👨‍🌾 आप क्या करते हैं? (किसान / मज़दूर / छात्र)\n• 💰 सालाना आय कितनी है?\n• 📍 कौन से राज्य में रहते हैं?\n• 🏷️ वर्ग क्या है? (General / OBC / SC / ST)\n\nइन जानकारियों के बाद मैं **आपके लिए best schemes** बताऊंगा!\n\n⚡ **त्वरित जाँच:**\n• किसान: pmkisan.gov.in\n• स्वास्थ्य: pmjay.gov.in\n• आवास: pmaymis.gov.in`,
    sources: ["pm_kisan.pdf", "ayushman.pdf"],
    profile: {},
  },
  documents: {
    text: `📄 **जरूरी दस्तावेज़**\n\n**सभी schemes के लिए:**\n• ✅ आधार कार्ड (सबसे जरूरी)\n• ✅ बैंक पासबुक\n• ✅ मोबाइल नंबर (आधार से linked)\n\n**PM Kisan के लिए:**\n• जमीन के कागज (खसरा/खतौनी)\n\n**आयुष्मान के लिए:**\n• राशन कार्ड / SECC डेटा\n\n**PM आवास के लिए:**\n• आय प्रमाण पत्र, संपत्ति के दस्तावेज़\n\n💡 **टिप:** आधार को मोबाइल से link करना जरूरी है!`,
    sources: ["pm_kisan.pdf", "ayushman.pdf"],
    profile: {},
  },
  apply: {
    text: `📝 **आवेदन कैसे करें?**\n\n**Online तरीका:**\n1. Official website खोलें\n2. "New Registration" click करें\n3. आधार नंबर से login करें\n4. फॉर्म भरें\n5. दस्तावेज़ upload करें और submit करें\n\n**Offline तरीका:**\n• 🏢 ग्राम पंचायत जाएं\n• 🖥️ CSC Centre (मुफ़्त मदद)\n• 🏦 बैंक ब्रांच\n\n**Helplines:**\n• PM Kisan: 📞 155261\n• Ayushman: 📞 14555\n• PM Awas: 📞 1800-11-6163`,
    sources: ["pm_kisan.pdf"],
    profile: {},
  },
  default: {
    text: `🙏 **नमस्ते! मैं हूँ सरकारी मित्र**\n\nमैं आपको government schemes की जानकारी देता हूँ!\n\n**मैं help कर सकता हूँ:**\n• 🌾 किसान योजनाएं (PM Kisan, Fasal Bima)\n• 🏥 स्वास्थ्य योजनाएं (Ayushman Bharat)\n• 🏠 आवास योजनाएं (PM Awas)\n• ✅ पात्रता जांचना\n• 📋 आवेदन के steps\n\n*नीचे के buttons से शुरू करें!* 👇`,
    sources: [],
    profile: {},
  },
};

export function getBotResponse(message) {
  const lower = message.toLowerCase();
  if (lower.includes("kisan") || lower.includes("farmer") || lower.includes("किसान") || lower.includes("fasal") || lower.includes("फसल"))
    return BOT_RESPONSES["pm kisan"];
  if (lower.includes("ayushman") || lower.includes("health") || lower.includes("स्वास्थ्य") || lower.includes("sehat") || lower.includes("ilaaj"))
    return BOT_RESPONSES.ayushman;
  if (lower.includes("awas") || lower.includes("ghar") || lower.includes("घर") || lower.includes("housing") || lower.includes("makaan"))
    return BOT_RESPONSES.awas;
  if (lower.includes("document") || lower.includes("kagaz") || lower.includes("दस्तावेज") || lower.includes("papers") || lower.includes("aadhaar"))
    return BOT_RESPONSES.documents;
  if (lower.includes("apply") || lower.includes("aavedan") || lower.includes("आवेदन") || lower.includes("kaise") || lower.includes("karna"))
    return BOT_RESPONSES.apply;
  if (lower.includes("eligib") || lower.includes("patr") || lower.includes("पात्र") || lower.includes("konsi") || lower.includes("milegi") || lower.includes("scheme"))
    return BOT_RESPONSES.eligibility;
  return BOT_RESPONSES.default;
}

export const MOCK_PROFILE = {
  age: null,
  income: null,
  profession: null,
  state: null,
  category: null,
  gender: null,
};