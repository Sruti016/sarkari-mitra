import requests
import os
from dotenv import load_dotenv
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
# Local schemes database - No API needed!

SCHEMES_DATABASE = {
    "mudra": {
        "title": "PM Mudra Yojana",
        "snippet": "PM Mudra Yojana ke tahat 10 lakh rupaye tak ka loan milta hai business shuru karne ke liye. Teen categories hain: Shishu (50,000 tak), Kishor (5 lakh tak), Tarun (10 lakh tak). Koi collateral nahi chahiye.",
        "eligibility": "18+ age, Indian citizen, small business owner",
        "documents": "Aadhaar, PAN, business proof, address proof",
        "link": "https://www.mudra.org.in"
    },
    "sukanya": {
        "title": "Sukanya Samriddhi Yojana",
        "snippet": "Beti ke liye savings scheme. 7.6% annual interest milta hai. 10 saal se kam umar ki beti ke naam account khul sakta hai. 15 saal tak paise jama karo, 21 saal mein mature hoti hai.",
        "eligibility": "10 saal se kam umar ki beti, Indian citizen",
        "documents": "Beti ka birth certificate, parents ka Aadhaar, address proof",
        "link": "https://www.indiapost.gov.in"
    },
    "atal pension": {
        "title": "Atal Pension Yojana",
        "snippet": "Asangathit kshetra ke workers ke liye pension scheme. 60 saal ke baad 1000 se 5000 rupaye monthly pension milti hai. 18-40 saal ke log join kar sakte hain.",
        "eligibility": "18-40 saal, bank account hona chahiye",
        "documents": "Aadhaar, bank account, mobile number",
        "link": "https://npscra.nsdl.co.in"
    },
    "mgnrega": {
        "title": "MGNREGA - Mahatma Gandhi National Rural Employment Guarantee",
        "snippet": "Gramin parivaron ko saal mein 100 din ka rozgar guarantee milta hai. Minimum wages milti hain. Job card banwana padta hai.",
        "eligibility": "Rural area mein rehne wale adult",
        "documents": "Aadhaar, address proof, photo",
        "link": "https://nrega.nic.in"
    },
    "ujjwala": {
        "title": "PM Ujjwala Yojana",
        "snippet": "BPL parivaron ko free LPG connection milta hai. Mahilaon ke naam connection diya jata hai. Deposit free connection aur pehla refill free milta hai.",
        "eligibility": "BPL family, mahila ke naam",
        "documents": "BPL card, Aadhaar, address proof",
        "link": "https://pmuy.gov.in"
    },
    "jan dhan": {
        "title": "PM Jan Dhan Yojana",
        "snippet": "Zero balance bank account scheme. 2 lakh rupaye ka accident insurance, 30,000 life insurance, overdraft facility milti hai. RuPay debit card bhi milta hai.",
        "eligibility": "Koi bhi Indian citizen jiske paas bank account nahi hai",
        "documents": "Aadhaar ya koi bhi ID proof",
        "link": "https://pmjdy.gov.in"
    },
    "fasal bima": {
        "title": "PM Fasal Bima Yojana",
        "snippet": "Kisan ki fasal ko prakritik aapda se protection milti hai. Bahut kam premium pe insurance milta hai. Rabi, Kharif, aur commercial crops covered hain.",
        "eligibility": "Koi bhi kisan - loanee aur non-loanee dono",
        "documents": "Aadhaar, bank account, khasra number, bowing certificate",
        "link": "https://pmfby.gov.in"
    },
    "awas": {
        "title": "PM Awas Yojana",
        "snippet": "Garib parivaron ko pakka ghar banane ke liye 1.2 lakh (rural) ya 2.5 lakh (urban) ki madad milti hai. Home loan pe interest subsidy bhi milti hai.",
        "eligibility": "EWS/LIG/MIG category, pehle se pakka ghar na ho",
        "documents": "Aadhaar, income certificate, bank account",
        "link": "https://pmaymis.gov.in"
    },
    "kisan": {
        "title": "PM Kisan Samman Nidhi",
        "snippet": "Kisan parivaron ko saal mein 6000 rupaye milte hain - 3 installments mein 2000-2000 karke. Seedha bank account mein aate hain.",
        "eligibility": "Chhote aur seemaant kisan jinke paas 2 hectare tak zameen ho",
        "documents": "Aadhaar, bank account, khasra/khatauni",
        "link": "https://pmkisan.gov.in"
    },
    "scholarship": {
        "title": "National Scholarship Portal - Scholarships",
        "snippet": "Students ke liye kai scholarships available hain - Pre-matric, Post-matric, Merit cum Means. SC/ST/OBC/minority students ke liye alag alag schemes hain.",
        "eligibility": "Students, income limit alag alag hai",
        "documents": "Aadhaar, marksheet, income certificate, caste certificate",
        "link": "https://scholarships.gov.in"
    },
    "vishwakarma": {
        "title": "PM Vishwakarma Yojana",
        "snippet": "Kaarigaron aur haath se kaam karne walon ke liye scheme. 3 lakh rupaye tak ka loan sirf 5% interest par milta hai. Free training, toolkit aur certificate bhi milta hai.",
        "eligibility": "18+ age, traditional craft/trade karne wale log — darzi, lohar, kumhar, carpenter, etc.",
        "documents": "Aadhaar, mobile number, bank account",
        "link": "https://pmvishwakarma.gov.in"
    },
    "startup india": {
        "title": "Startup India Scheme",
        "snippet": "Naye businesses ke liye government support. 3 saal tak income tax exemption, fast patent registration, Rs 10,000 crore fund available hai.",
        "eligibility": "10 saal se kam purana business, innovative product/service",
        "documents": "Business registration, PAN, Aadhaar",
        "link": "https://startupindia.gov.in"
    },
    "beti bachao": {
        "title": "Beti Bachao Beti Padhao",
        "snippet": "Beti ki education aur safety ke liye scheme. Sukanya Samriddhi account ke saath milkar kaam karta hai. Free education, scholarship aur awareness programs.",
        "eligibility": "0-10 saal ki beti wale parents",
        "documents": "Beti ka birth certificate, parents ka Aadhaar",
        "link": "https://wcd.nic.in"
    },
    "svanidhi": {
        "title": "PM SVANidhi Scheme",
        "snippet": "Street vendors ke liye working capital loan. Pehli baar 10,000 rupaye, phir 20,000 aur 50,000 tak milte hain. Digital payment pe cashback bhi milta hai.",
        "eligibility": "Street vendors, rehri wale, footpath dukandaar",
        "documents": "Aadhaar, vendor certificate ya letter of recommendation",
        "link": "https://pmsvanidhi.mohua.gov.in"
    },
    "stand up india": {
        "title": "Stand Up India",
        "snippet": "SC/ST aur mahilaon ke liye business loan. 10 lakh se 1 crore rupaye tak ka loan milta hai greenfield enterprise ke liye.",
        "eligibility": "SC/ST ya mahila, 18+ age, greenfield project",
        "documents": "Aadhaar, PAN, caste certificate, business plan",
        "link": "https://standupmitra.in"
    },
    "pm kaushal": {
        "title": "PM Kaushal Vikas Yojana",
        "snippet": "Free skill training scheme. 300+ courses available hain. Training ke baad certificate aur placement assistance milti hai. Stipend bhi milta hai.",
        "eligibility": "18-35 age, 10th pass",
        "documents": "Aadhaar, marksheet, bank account",
        "link": "https://pmkvyofficial.org"
    }
}
import os
from dotenv import load_dotenv
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_latest_schemes(query: str) -> str:
    """
    NewsAPI se latest government schemes fetch karo
    """
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query + " government scheme India",
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 3
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get("status") != "ok":
            return ""

        articles = data.get("articles", [])
        if not articles:
            return ""

        result = "\n[Latest News]\n"
        for a in articles:
            result += f"\n• {a.get('title', '')}\n"
            result += f"  {a.get('description', '')}\n"

        return result

    except Exception as e:
        print(f"News fetch error: {e}")
        return ""

def search_schemes(query: str, num_results: int = 3):
    """
    Local database se schemes dhundho
    """
    query_lower = query.lower()
    results = []
    
    for key, scheme in SCHEMES_DATABASE.items():
        if key in query_lower or any(word in query_lower for word in key.split()):
            results.append({
                "title": scheme["title"],
                "snippet": f"{scheme['snippet']}\nEligibility: {scheme['eligibility']}\nDocuments: {scheme['documents']}",
                "link": scheme["link"]
            })
    
    # Agar koi match nahi mila toh top 2 schemes return karo
    if not results:
        for key, scheme in list(SCHEMES_DATABASE.items())[:2]:
            results.append({
                "title": scheme["title"],
                "snippet": scheme["snippet"],
                "link": scheme["link"]
            })
    
    return results[:num_results]


def format_search_results(results: list) -> str:
    """
    Search results ko readable format mein convert karo
    """
    if not results:
        return ""
    
    formatted = "\n\n[Additional Scheme Information]\n"
    for i, r in enumerate(results, 1):
        formatted += f"\n{i}. {r['title']}\n"
        formatted += f"   {r['snippet']}\n"
        if r['link']:
            formatted += f"   Official Link: {r['link']}\n"
    
    return formatted