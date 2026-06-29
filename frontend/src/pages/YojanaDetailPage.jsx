import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { YOJANA_DETAILS, t }      from "../utils/staticData";
import { load }                    from "../utils/storage";

const TABS = [
  { id:"overview",   hi:"जानकारी",   en:"Overview",   mix:"Jankari"   },
  { id:"eligibility",hi:"पात्रता",   en:"Eligibility",mix:"Eligibility"},
  { id:"documents",  hi:"दस्तावेज़", en:"Documents",  mix:"Documents"  },
  { id:"apply",      hi:"आवेदन",     en:"Apply",      mix:"Apply"      },
];

function CheckItem({ hi, en, lang }) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0">
      <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="#16a34a" strokeWidth="3">
          <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      <p className="text-[15px] text-gray-700 leading-relaxed font-medium">{t(lang, hi, en, en)}</p>
    </div>
  );
}

function DocItem({ hi, en, lang, index }) {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-gray-100 last:border-0">
      <div className="w-8 h-8 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0 font-bold text-blue-700 text-[13px]">
        {index + 1}
      </div>
      <p className="text-[15px] text-gray-700 font-medium">{t(lang, hi, en, en)}</p>
    </div>
  );
}

function StepItem({ hi, en, lang, index }) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0">
      <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-white text-[13px] mt-0.5"
        style={{ background: "linear-gradient(135deg,#16a34a,#15803d)", flexShrink: 0 }}>
        {index + 1}
      </div>
      <p className="text-[15px] text-gray-700 leading-relaxed font-medium pt-1">{t(lang, hi, en, en)}</p>
    </div>
  );
}

export default function YojanaDetailPage() {
  const { id }   = useParams();
  const navigate = useNavigate();
  const lang     = load("sm_lang", "hi");
  const [tab, setTab] = useState("overview");

  const y = YOJANA_DETAILS[id];

  if (!y) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4 bg-gray-50 text-center px-6"
        style={{ fontFamily: "system-ui,sans-serif" }}>
        <p className="text-5xl">😕</p>
        <p className="text-[18px] font-bold text-gray-800">
          {t(lang, "Yojana नहीं मिली", "Yojana not found", "Yojana nahi mili")}
        </p>
        <button onClick={() => navigate(-1)}
          className="px-6 py-3 bg-green-600 text-white rounded-2xl font-bold active:scale-95 transition-all">
          {t(lang, "वापस जाएं", "Go Back", "Wapas Jao")}
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50"
      style={{ fontFamily: "'Noto Sans','Hind',system-ui,sans-serif" }}>

      {/* ── Hero Header ── */}
      <div className="flex-shrink-0"
        style={{ background: `linear-gradient(135deg, ${y.color}dd, ${y.color})`,
          boxShadow: `0 4px 20px ${y.color}44` }}>
        <div className="max-w-5xl mx-auto px-6 py-5">
          {/* Back */}
          <div className="flex items-center gap-3 mb-4">
            <button onClick={() => navigate(-1)}
              className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-white hover:bg-white/30 transition-all active:scale-90 flex-shrink-0">
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path d="M19 12H5M12 5l-7 7 7 7" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
            <p className="text-white/80 text-[13px] font-medium">
              {t(lang, "योजना विवरण", "Scheme Details", "Yojana Detail")}
            </p>
          </div>

          {/* Hero info — side by side on desktop */}
          <div className="flex items-start gap-6">
            <div className="flex items-center gap-4 flex-1">
              <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center text-4xl shadow-lg flex-shrink-0">
                {y.icon}
              </div>
              <div>
                <h1 className="text-white font-bold text-[22px] leading-tight">{y.name}</h1>
                <p className="text-white/70 text-[13px] mt-0.5">
                  {t(lang, y.ministry, y.ministryEn, y.ministryEn)}
                </p>
              </div>
            </div>

            {/* Benefit highlight */}
            <div className="bg-white/20 backdrop-blur rounded-2xl p-4" style={{ minWidth: "220px" }}>
              <p className="text-white/70 text-[11px] font-semibold uppercase tracking-wider mb-1">
                {t(lang, "मुख्य लाभ", "Key Benefit", "Key Benefit")}
              </p>
              <p className="text-white font-bold text-[22px]">
                {t(lang, y.benefit, y.benefitEn, y.benefitEn)}
              </p>
              <p className="text-white/80 text-[13px] mt-0.5">
                {t(lang, y.benefitDesc, y.benefitDescEn, y.benefitDescEn)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Tab navigation ── */}
      <div className="bg-white border-b border-gray-100 flex-shrink-0">
        <div className="max-w-5xl mx-auto px-6 flex">
          {TABS.map(tb => (
            <button key={tb.id} onClick={() => setTab(tb.id)}
              className={`px-6 py-4 text-[14px] font-bold whitespace-nowrap transition-all border-b-2
                ${tab === tb.id
                  ? "border-green-600 text-green-700 bg-green-50"
                  : "border-transparent text-gray-500 hover:text-gray-700"}`}>
              {t(lang, tb.hi, tb.en, tb.mix)}
            </button>
          ))}
        </div>
      </div>

      {/* ── Tab Content ── */}
      <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-6">

        {/* Overview tab */}
        {tab === "overview" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Helpline */}
            <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
              <p className="text-[12px] font-bold text-gray-400 uppercase tracking-wider mb-3">
                {t(lang, "Helpline Number", "Helpline Number", "Helpline Number")}
              </p>
              <a href={`tel:${y.helpline}`} className="flex items-center gap-3 active:scale-95 transition-all">
                <div className="w-11 h-11 rounded-xl bg-green-100 flex items-center justify-center text-2xl">📞</div>
                <div>
                  <p className="font-bold text-[20px] text-green-700">{y.helpline}</p>
                  <p className="text-[12px] text-gray-500">
                    {t(lang, "मुफ़्त • tap करके call करें", "Free • Tap to call", "Free • Tap karke call karein")}
                  </p>
                </div>
              </a>
            </div>

            {/* Website */}
            <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
              <p className="text-[12px] font-bold text-gray-400 uppercase tracking-wider mb-3">
                {t(lang, "Official Website", "Official Website", "Official Website")}
              </p>
              <a href={`https://${y.link}`} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-3 active:scale-95 transition-all">
                <div className="w-11 h-11 rounded-xl bg-blue-100 flex items-center justify-center text-2xl">🌐</div>
                <div>
                  <p className="font-bold text-[15px] text-blue-700">{y.link}</p>
                  <p className="text-[12px] text-gray-500">
                    {t(lang, "tap करके खोलें", "Tap to open", "Tap karke kholein")}
                  </p>
                </div>
              </a>
            </div>

            {/* Quick stats */}
            <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
              <p className="text-[12px] font-bold text-gray-400 uppercase tracking-wider mb-3">
                {t(lang, "जानकारी", "Information", "Jankari")}
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-xl p-3 text-center">
                  <p className="text-2xl mb-1">{y.eligibility.length}+</p>
                  <p className="text-[11px] text-gray-500 font-medium">
                    {t(lang, "पात्रता शर्तें", "Eligibility Criteria", "Eligibility Criteria")}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-xl p-3 text-center">
                  <p className="text-2xl mb-1">{y.documents.length}</p>
                  <p className="text-[11px] text-gray-500 font-medium">
                    {t(lang, "दस्तावेज़ जरूरी", "Docs Required", "Docs Required")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Eligibility tab */}
        {tab === "eligibility" && (
          <div className="max-w-2xl">
            <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
              <p className="text-[14px] font-bold text-gray-500 mb-2">
                {t(lang, "इनमें से सब होना चाहिए:", "All of these must apply:", "Ye sab hona chahiye:")}
              </p>
              {y.eligibility.map((item, i) => (
                <CheckItem key={i} hi={item.hi} en={item.en} lang={lang} />
              ))}
            </div>
          </div>
        )}

        {/* Documents tab */}
        {tab === "documents" && (
          <div className="max-w-2xl">
            <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm mb-4">
              {y.documents.map((doc, i) => (
                <DocItem key={i} hi={doc.hi} en={doc.en} lang={lang} index={i} />
              ))}
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4">
              <p className="text-[13px] text-amber-800 font-medium leading-relaxed">
                💡 {t(lang,
                  "सभी दस्तावेज़ की original + photocopy दोनों लेकर जाएं",
                  "Carry both original + photocopy of all documents",
                  "Sab documents ki original + photocopy dono lekar jayen"
                )}
              </p>
            </div>
          </div>
        )}

        {/* Apply tab */}
        {tab === "apply" && (
          <div className="max-w-2xl">
            <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm mb-4">
              {y.steps.map((step, i) => (
                <StepItem key={i} hi={step.hi} en={step.en} lang={lang} index={i} />
              ))}
            </div>
            <div className="bg-green-50 border border-green-200 rounded-2xl p-4">
              <p className="text-[13px] text-green-800 font-medium leading-relaxed">
                💡 {t(lang,
                  "मुफ़्त मदद के लिए नज़दीकी CSC Centre जाएं — वे आपकी पूरी मदद करेंगे",
                  "Visit nearest CSC Centre for free help — they will assist you completely",
                  "Free help ke liye nearest CSC Centre jayen — woh poori madad karenge"
                )}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* ── CTA Footer ── */}
      <div className="px-6 py-4 bg-white border-t border-gray-100 flex-shrink-0">
        <div className="max-w-5xl mx-auto flex gap-3">
          <button onClick={() => navigate("/")}
            className="flex items-center justify-center gap-2 px-8 py-3 rounded-2xl font-bold text-[14px] text-green-700 border-2 border-green-300 bg-green-50 active:scale-95 transition-all hover:bg-green-100">
            💬 {t(lang, "Chat करें", "Chat Now", "Chat Karein")}
          </button>
          <a href={`https://${y.link}`} target="_blank" rel="noopener noreferrer"
            className="flex items-center justify-center px-8 py-3 rounded-2xl font-bold text-[14px] text-white active:scale-95 transition-all shadow-lg"
            style={{ background: `linear-gradient(135deg,${y.color},${y.color}cc)`,
              boxShadow: `0 4px 12px ${y.color}44` }}>
            {t(lang, "Apply करें →", "Apply Now →", "Apply Karo →")}
          </a>
        </div>
      </div>
    </div>
  );
}