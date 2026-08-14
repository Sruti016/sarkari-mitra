import React, { useState } from "react";
import { useNavigate }      from "react-router-dom";
import { SCHEME_CARDS, t }  from "../utils/staticData";
import { load }              from "../utils/storage";

const FILTERS = [
  { id: "all",     hi: "सभी",       en: "All",     mix: "Sab"     },
  { id: "farmer",  hi: "किसान",     en: "Farmer",  mix: "Kisan"   },
  { id: "health",  hi: "स्वास्थ्य", en: "Health",  mix: "Health"  },
  { id: "housing", hi: "आवास",      en: "Housing", mix: "Housing" },
  { id: "other",   hi: "अन्य",      en: "Other",   mix: "Other"   },
];

const ELIGIBLE_CONFIG = {
  yes:   { hi:"✅ पात्र",  en:"✅ Eligible", mix:"✅ Eligible", badge:"bg-green-600",  card:"bg-green-50",  border:"border-green-200" },
  maybe: { hi:"⚠️ शायद",  en:"⚠️ Maybe",   mix:"⚠️ Maybe",   badge:"bg-amber-500",  card:"bg-amber-50",  border:"border-amber-200" },
  no:    { hi:"❌ नहीं",   en:"❌ No",       mix:"❌ Nahi",     badge:"bg-red-600",    card:"bg-red-50",    border:"border-red-200"   },
};

function SchemeCard({ scheme, lang, onLearnMore }) {
  const cfg = ELIGIBLE_CONFIG[scheme.eligible];
  return (
    <div className={`${cfg.card} ${cfg.border} border-2 rounded-2xl p-4 transition-all hover:shadow-md`}>
      {/* Top row */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-11 h-11 rounded-2xl bg-white border border-gray-100 flex items-center justify-center text-2xl shadow-sm flex-shrink-0">
            {scheme.icon}
          </div>
          <div>
            <h3 className="font-bold text-gray-900 text-[15px] leading-snug">{scheme.name}</h3>
            <p className="text-[11px] text-gray-500 mt-0.5">{scheme.ministry} मंत्रालय</p>
          </div>
        </div>
        <span className={`${cfg.badge} text-white text-[11px] font-bold px-2.5 py-1.5 rounded-full whitespace-nowrap flex-shrink-0 shadow-sm`}>
          {t(lang, cfg.hi, cfg.en, cfg.mix)}
        </span>
      </div>

      {/* Benefit */}
      <div className="bg-white rounded-xl px-3 py-2.5 mb-3 border border-gray-100">
        <p className="text-[11px] text-gray-500 mb-0.5">{t(lang, "लाभ", "Benefit", "Benefit")}</p>
        <p className="font-bold text-gray-900 text-[16px]">
          {t(lang, scheme.benefit, scheme.benefitEn, scheme.benefitEn)}
        </p>
      </div>

      {/* Reason */}
      <p className="text-[13px] text-gray-600 mb-3">
        {t(lang, scheme.reasonHi, scheme.reasonEn, scheme.reasonEn)}
      </p>

      {/* Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => onLearnMore(scheme.yojanaId)}
          className="flex-1 py-2.5 rounded-xl font-bold text-[13px] text-green-700 bg-white border-2 border-green-300 transition-all hover:bg-green-50 active:scale-95">
          {t(lang, "और जानें", "Learn More", "Aur Jaano")}
        </button>
        <a
          href={`https://${scheme.link}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 py-2.5 rounded-xl font-bold text-[13px] text-white text-center transition-all shadow-md active:scale-95"
          style={{ background: "linear-gradient(135deg,#16a34a,#15803d)", boxShadow: "0 4px 10px rgba(22,163,74,0.25)" }}>
          {t(lang, "Apply करें →", "Apply Now →", "Apply Karo →")}
        </a>
      </div>
    </div>
  );
}

export default function SchemesPage() {
  const navigate = useNavigate();
  const lang     = load("sm_lang", "hi");
  const [filter, setFilter] = useState("all");

  const filtered = filter === "all" ? SCHEME_CARDS : SCHEME_CARDS.filter(s => s.category === filter);
  const eligible      = SCHEME_CARDS.filter(s => s.eligible === "yes").length;
  const maybeEligible = SCHEME_CARDS.filter(s => s.eligible === "maybe").length;

  return (
    <div className="flex flex-col bg-gray-50 min-h-screen"
      style={{ fontFamily: "'Noto Sans','Hind',system-ui,sans-serif" }}>

      {/* ── Header ── */}
      <div className="flex-shrink-0"
        style={{ background: "linear-gradient(135deg,#14532d,#166534)", boxShadow: "0 4px 16px rgba(20,83,45,0.3)" }}>
        <div className="max-w-6xl mx-auto px-6">
          {/* Top bar */}
          <div className="flex items-center gap-3 py-4">
            <button onClick={() => navigate(-1)}
              className="w-9 h-9 rounded-full bg-white/15 flex items-center justify-center text-white hover:bg-white/25 transition-all active:scale-90 flex-shrink-0">
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path d="M19 12H5M12 5l-7 7 7 7" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
            <div className="flex-1">
              <h1 className="text-white font-bold text-[20px] leading-tight">
                {t(lang, "सरकारी योजनाएं", "Government Schemes", "Sarkari Yojanaen")}
              </h1>
              <p className="text-green-300 text-[13px]">
                {t(lang, "आपके प्रोफ़ाइल के अनुसार", "Based on your profile", "Aapke profile ke hisaab se")}
              </p>
            </div>
            {/* Summary chips */}
            <div className="flex gap-3">
              <div className="flex items-center gap-2 bg-white/10 rounded-full px-3 py-1.5">
                <div className="w-2 h-2 rounded-full bg-green-400" />
                <span className="text-white text-[12px] font-bold">{eligible} {t(lang, "पात्र", "Eligible", "Eligible")}</span>
              </div>
              <div className="flex items-center gap-2 bg-white/10 rounded-full px-3 py-1.5">
                <div className="w-2 h-2 rounded-full bg-amber-400" />
                <span className="text-white text-[12px] font-bold">{maybeEligible} {t(lang, "शायद", "Maybe", "Maybe")}</span>
              </div>
              <div className="flex items-center gap-2 bg-white/10 rounded-full px-3 py-1.5">
                <span className="text-white text-[12px] font-bold">{SCHEME_CARDS.length} {t(lang, "कुल", "Total", "Total")}</span>
              </div>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="flex gap-2 pb-4 overflow-x-auto" style={{ scrollbarWidth: "none" }}>
            {FILTERS.map(f => (
              <button key={f.id} onClick={() => setFilter(f.id)}
                className={`px-5 py-2 rounded-full text-[13px] font-bold whitespace-nowrap transition-all active:scale-95
                  ${filter === f.id
                    ? "bg-white text-green-800 shadow-md"
                    : "bg-white/15 text-white hover:bg-white/25"}`}>
                {t(lang, f.hi, f.en, f.mix)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Cards Grid ── */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-6 py-6">
        {filtered.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <p className="text-5xl mb-4">🔍</p>
            <p className="text-[16px] font-semibold">
              {t(lang, "इस category में कोई scheme नहीं", "No schemes in this category", "Is category mein koi scheme nahi")}
            </p>
          </div>
        ) : (
          <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))" }}>
            {filtered.map(s => (
              <SchemeCard key={s.id} scheme={s} lang={lang}
                onLearnMore={(id) => navigate(`/yojana/${id}`)} />
            ))}
          </div>
        )}

        {/* Disclaimer */}
        <div className="mt-6 mb-4 p-4 bg-amber-50 border border-amber-200 rounded-2xl max-w-2xl mx-auto">
          <p className="text-[13px] text-amber-800 text-center leading-relaxed font-medium">
            ⚠️ {t(lang,
              "Apply करने से पहले official government portal पर eligibility ज़रूर verify करें",
              "Always verify eligibility on official government portal before applying",
              "Apply karne se pehle official portal pe eligibility zaroor verify karein"
            )}
          </p>
        </div>
      </div>

      {/* ── Back to chat ── */}
      <div className="px-6 py-4 bg-white border-t border-gray-100 flex-shrink-0">
        <div className="max-w-6xl mx-auto">
          <button onClick={() => navigate("/")}
            className="flex items-center justify-center gap-2 px-8 py-3 rounded-2xl font-bold text-[15px] active:scale-95 transition-all text-green-700 border-2 border-green-300 bg-green-50 hover:bg-green-100">
            💬 {t(lang, "Chat पर वापस जाएं", "Back to Chat", "Chat pe wapas jao")}
          </button>
        </div>
      </div>
    </div>
  );
}