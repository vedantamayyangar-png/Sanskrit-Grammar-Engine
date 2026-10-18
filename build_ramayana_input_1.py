# -*- coding: utf-8 -*-
"""Build Devanagari word-list input for sandhi_splitter.py from all 79
slokas of sa_rAmAyaNa.txt Balakanda Sarga 1 (R_1,001.001-079), using
the indic_transliteration library's verified IAST->Devanagari converter
(avoids hand-typing Devanagari, the exact mistake class already caught
once in this session). IAST text below is copied verbatim from the
source file (E:\\Sanskrit & Tamil Scholarship\\01_Ramayana_Project\\
source_texts\\sa_rAmAyaNa.txt, lines 34-273), not retyped from memory."""
import argparse
import sys

from indic_transliteration import sanscript

VERSES = {
    "R_1,001.001": "tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam "
                   "nāradaṃ paripapraccha vālmīkir munipuṃgavam",
    "R_1,001.002": "ko nv asmin sāmprataṃ loke guṇavān kaś ca vīryavān "
                   "dharmajñaś ca kṛtajñaś ca satyavākyo dṛḍhavrataḥ",
    "R_1,001.003": "cāritreṇa ca ko yuktaḥ sarvabhūteṣu ko hitaḥ "
                   "vidvān kaḥ kaḥ samarthaś ca kaś caikapriyadarśanaḥ",
    "R_1,001.004": "ātmavān ko jitakrodho dyutimān ko 'nasūyakaḥ "
                   "kasya bibhyati devāś ca jātaroṣasya saṃyuge",
    "R_1,001.005": "etad icchāmy ahaṃ śrotuṃ paraṃ kautūhalaṃ hi me "
                   "maharṣe tvaṃ samartho 'si jñātum evaṃvidhaṃ naram",
    "R_1,001.006": "śrutvā caitat trilokajño vālmīker nārado vacaḥ "
                   "śrūyatām iti cāmantrya prahṛṣṭo vākyam abravīt",
    "R_1,001.007": "bahavo durlabhāś caiva ye tvayā kīrtitā guṇāḥ "
                   "mune vakṣyāmy ahaṃ buddhvā tair yuktaḥ śrūyatāṃ naraḥ",
    "R_1,001.008": "ikṣvākuvaṃśaprabhavo rāmo nāma janaiḥ śrutaḥ "
                   "niyatātmā mahāvīryo dyutimān dhṛtimān vaśī",
    "R_1,001.009": "buddhimān nītimān vāgmī śrīmāñ śatrunibarhaṇaḥ "
                   "vipulāṃso mahābāhuḥ kambugrīvo mahāhanuḥ",
    "R_1,001.010": "mahorasko maheṣvāso gūḍhajatrur ariṃdamaḥ "
                   "ājānubāhuḥ suśirāḥ sulalāṭaḥ suvikramaḥ",
    "R_1,001.011": "samaḥ samavibhaktāṅgaḥ snigdhavarṇaḥ pratāpavān "
                   "pīnavakṣā viśālākṣo lakṣmīvāñ śubhalakṣaṇaḥ",
    "R_1,001.012": "dharmajñaḥ satyasaṃdhaś ca prajānāṃ ca hite rataḥ "
                   "yaśasvī jñānasaṃpannaḥ śucir vaśyaḥ samādhimān",
    "R_1,001.013": "rakṣitā jīvalokasya dharmasya parirakṣitā "
                   "vedavedāṅgatattvajño dhanurvede ca niṣṭhitaḥ",
    "R_1,001.014": "sarvaśāstrārthatattvajña smṛtimān pratibhānavān "
                   "sarvalokapriyaḥ sādhur adīnātmā vicakṣaṇaḥ",
    "R_1,001.015": "sarvadābhigataḥ sadbhiḥ samudra iva sindhubhiḥ "
                   "āryaḥ sarvasamaś caiva sadaikapriyadarśanaḥ",
    "R_1,001.016": "sa ca sarvaguṇopetaḥ kausalyānandavardhanaḥ "
                   "samudra iva gāmbhīrye dhairyeṇa himavān iva",
    "R_1,001.017": "viṣṇunā sadṛśo vīrye somavat priyadarśanaḥ "
                   "kālāgnisadṛśaḥ krodhe kṣamayā pṛthivīsamaḥ",
    "R_1,001.018": "dhanadena samas tyāge satye dharma ivāparaḥ "
                   "tam evaṃguṇasaṃpannaṃ rāmaṃ satyaparākramam",
    "R_1,001.019": "jyeṣṭhaṃ śreṣṭhaguṇair yuktaṃ priyaṃ daśarathaḥ sutam "
                   "yauvarājyena saṃyoktum aicchat prītyā mahīpatiḥ",
    "R_1,001.020": "tasyābhiṣekasaṃbhārān dṛṣṭvā bhāryātha kaikayī "
                   "pūrvaṃ dattavarā devī varam enam ayācata "
                   "vivāsanaṃ ca rāmasya bharatasyābhiṣecanam",
    "R_1,001.021": "sa satyavacanād rājā dharmapāśena saṃyataḥ "
                   "vivāsayām āsa sutaṃ rāmaṃ daśarathaḥ priyam",
    "R_1,001.022": "sa jagāma vanaṃ vīraḥ pratijñām anupālayan "
                   "pitur vacananirdeśāt kaikeyyāḥ priyakāraṇāt",
    "R_1,001.023": "taṃ vrajantaṃ priyo bhrātā lakṣmaṇo 'nujagāma ha "
                   "snehād vinayasaṃpannaḥ sumitrānandavardhanaḥ",
    "R_1,001.024": "sarvalakṣaṇasaṃpannā nārīṇām uttamā vadhūḥ "
                   "sītāpy anugatā rāmaṃ śaśinaṃ rohiṇī yathā",
    "R_1,001.025": "paurair anugato dūraṃ pitrā daśarathena ca "
                   "śṛṅgaverapure sūtaṃ gaṅgākūle vyasarjayat",
    "R_1,001.026": "te vanena vanaṃ gatvā nadīs tīrtvā bahūdakāḥ "
                   "citrakūṭam anuprāpya bharadvājasya śāsanāt",
    "R_1,001.027": "ramyam āvasathaṃ kṛtvā ramamāṇā vane trayaḥ "
                   "devagandharvasaṃkāśās tatra te nyavasan sukham",
    "R_1,001.028": "citrakūṭaṃ gate rāme putraśokāturas tadā "
                   "rājā daśarathaḥ svargaṃ jagāma vilapan sutam",
    "R_1,001.029": "mṛte tu tasmin bharato vasiṣṭhapramukhair dvijaiḥ "
                   "niyujyamāno rājyāya naicchad rājyaṃ mahābalaḥ "
                   "sa jagāma vanaṃ vīro rāmapādaprasādakaḥ",
    "R_1,001.030": "pāduke cāsya rājyāya nyāsaṃ dattvā punaḥ punaḥ "
                   "nivartayām āsa tato bharataṃ bharatāgrajaḥ",
    "R_1,001.031": "sa kāmam anavāpyaiva rāmapādāv upaspṛśan "
                   "nandigrāme 'karod rājyaṃ rāmāgamanakāṅkṣayā",
    "R_1,001.032": "rāmas tu punar ālakṣya nāgarasya janasya ca "
                   "tatrāgamanam ekāgre daṇḍakān praviveśa ha",
    "R_1,001.033": "virādhaṃ rākṣasaṃ hatvā śarabhaṅgaṃ dadarśa ha "
                   "sutīkṣṇaṃ cāpy agastyaṃ ca agastya bhrātaraṃ tathā",
    "R_1,001.034": "agastyavacanāc caiva jagrāhaindraṃ śarāsanam "
                   "khaḍgaṃ ca paramaprītas tūṇī cākṣayasāyakau",
    "R_1,001.035": "vasatas tasya rāmasya vane vanacaraiḥ saha "
                   "ṛṣayo 'bhyāgaman sarve vadhāyāsurarakṣasām",
    "R_1,001.036": "tena tatraiva vasatā janasthānanivāsinī "
                   "virūpitā śūrpaṇakhā rākṣasī kāmarūpiṇī",
    "R_1,001.037": "tataḥ śūrpaṇakhāvākyād udyuktān sarvarākṣasān "
                   "kharaṃ triśirasaṃ caiva dūṣaṇaṃ caiva rākṣasaṃ",
    "R_1,001.038": "nijaghāna raṇe rāmas teṣāṃ caiva padānugān "
                   "rakṣasāṃ nihatāny āsan sahasrāṇi caturdaśa",
    "R_1,001.039": "tato jñātivadhaṃ śrutvā rāvaṇaḥ krodhamūrchitaḥ "
                   "sahāyaṃ varayām āsa mārīcaṃ nāma rākṣasaṃ",
    "R_1,001.040": "vāryamāṇaḥ subahuśo mārīcena sa rāvaṇaḥ "
                   "na virodho balavatā kṣamo rāvaṇa tena te",
    "R_1,001.041": "anādṛtya tu tad vākyaṃ rāvaṇaḥ kālacoditaḥ "
                   "jagāma sahamārīcas tasyāśramapadaṃ tadā",
    "R_1,001.042": "tena māyāvinā dūram apavāhya nṛpātmajau "
                   "jahāra bhāryāṃ rāmasya gṛdhraṃ hatvā jaṭāyuṣam",
    "R_1,001.043": "gṛdhraṃ ca nihataṃ dṛṣṭvā hṛtāṃ śrutvā ca maithilīm "
                   "rāghavaḥ śokasaṃtapto vilalāpākulendriyaḥ",
    "R_1,001.044": "tatas tenaiva śokena gṛdhraṃ dagdhvā jaṭāyuṣam "
                   "mārgamāṇo vane sītāṃ rākṣasaṃ saṃdadarśa ha",
    "R_1,001.045": "kabandhaṃ nāma rūpeṇa vikṛtaṃ ghoradarśanam "
                   "taṃ nihatya mahābāhur dadāha svargataś ca saḥ",
    "R_1,001.046": "sa cāsya kathayām āsa śabarīṃ dharmacāriṇīm "
                   "śramaṇīṃ dharmanipuṇām abhigaccheti rāghava "
                   "so 'bhyagacchan mahātejāḥ śabarīṃ śatrusūdanaḥ",
    "R_1,001.047": "śabaryā pūjitaḥ samyag rāmo daśarathātmajaḥ "
                   "pampātīre hanumatā saṃgato vānareṇa ha",
    "R_1,001.048": "hanumadvacanāc caiva sugrīveṇa samāgataḥ "
                   "sugrīvāya ca tat sarvaṃ śaṃsad rāmo mahābalaḥ",
    "R_1,001.049": "tato vānararājena vairānukathanaṃ prati "
                   "rāmāyāveditaṃ sarvaṃ praṇayād duḥkhitena ca "
                   "vālinaś ca balaṃ tatra kathayām āsa vānaraḥ",
    "R_1,001.050": "pratijñātaṃ ca rāmeṇa tadā vālivadhaṃ prati "
                   "sugrīvaḥ śaṅkitaś cāsīn nityaṃ vīryeṇa rāghave",
    "R_1,001.051": "rāghavaḥ pratyayārthaṃ tu dundubheḥ kāyam uttamam "
                   "pādāṅguṣṭhena cikṣepa saṃpūrṇaṃ daśayojanam",
    "R_1,001.052": "bibheda ca punaḥ sālān saptaikena maheṣuṇā "
                   "giriṃ rasātalaṃ caiva janayan pratyayaṃ tadā",
    "R_1,001.053": "tataḥ prītamanās tena viśvastaḥ sa mahākapiḥ "
                   "kiṣkindhāṃ rāmasahito jagāma ca guhāṃ tadā",
    "R_1,001.054": "tato 'garjad dharivaraḥ sugrīvo hemapiṅgalaḥ "
                   "tena nādena mahatā nirjagāma harīśvaraḥ",
    "R_1,001.055": "tataḥ sugrīvavacanād dhatvā vālinam āhave "
                   "sugrīvam eva tad rājye rāghavaḥ pratyapādayat",
    "R_1,001.056": "sa ca sarvān samānīya vānarān vānararṣabhaḥ "
                   "diśaḥ prasthāpayām āsa didṛkṣur janakātmajām",
    "R_1,001.057": "tato gṛdhrasya vacanāt saṃpāter hanumān balī "
                   "śatayojanavistīrṇaṃ pupluve lavaṇārṇavam",
    "R_1,001.058": "tatra laṅkāṃ samāsādya purīṃ rāvaṇapālitām "
                   "dadarśa sītāṃ dhyāyantīm aśokavanikāṃ gatām",
    "R_1,001.059": "nivedayitvābhijñānaṃ pravṛttiṃ ca nivedya ca "
                   "samāśvāsya ca vaidehīṃ mardayām āsa toraṇam",
    "R_1,001.060": "pañca senāgragān hatvā sapta mantrisutān api "
                   "śūram akṣaṃ ca niṣpiṣya grahaṇaṃ samupāgamat",
    "R_1,001.061": "astreṇonmuham ātmānaṃ jñātvā paitāmahād varāt "
                   "marṣayan rākṣasān vīro yantriṇas tān yadṛcchayā",
    "R_1,001.062": "tato dagdhvā purīṃ laṅkām ṛte sītāṃ ca maithilīm "
                   "rāmāya priyam ākhyātuṃ punar āyān mahākapiḥ",
    "R_1,001.063": "so 'bhigamya mahātmānaṃ kṛtvā rāmaṃ pradakṣiṇam "
                   "nyavedayad ameyātmā dṛṣṭā sīteti tattvataḥ",
    "R_1,001.064": "tataḥ sugrīvasahito gatvā tīraṃ mahodadheḥ "
                   "samudraṃ kṣobhayām āsa śarair ādityasaṃnibhaiḥ",
    "R_1,001.065": "darśayām āsa cātmānaṃ samudraḥ saritāṃ patiḥ "
                   "samudravacanāc caiva nalaṃ setum akārayat",
    "R_1,001.066": "tena gatvā purīṃ laṅkāṃ hatvā rāvaṇam āhave "
                   "abhyaṣiñcat sa laṅkāyāṃ rākṣasendraṃ vibhīṣaṇam",
    "R_1,001.067": "karmaṇā tena mahatā trailokyaṃ sacarācaram "
                   "sadevarṣigaṇaṃ tuṣṭaṃ rāghavasya mahātmanaḥ",
    "R_1,001.068": "tathā paramasaṃtuṣṭaiḥ pūjitaḥ sarvadaivataiḥ "
                   "kṛtakṛtyas tadā rāmo vijvaraḥ pramumoda ha",
    "R_1,001.069": "devatābhyo varān prāpya samutthāpya ca vānarān "
                   "puṣpakaṃ tat samāruhya nandigrāmaṃ yayau tadā",
    "R_1,001.070": "nandigrāme jaṭāṃ hitvā bhrātṛbhiḥ sahito 'naghaḥ "
                   "rāmaḥ sītām anuprāpya rājyaṃ punar avāptavān",
    "R_1,001.071": "prahṛṣṭamudito lokas tuṣṭaḥ puṣṭaḥ sudhārmikaḥ "
                   "nirāyamo arogaś ca durbhikṣabhayavarjitaḥ",
    "R_1,001.072": "na putramaraṇaṃ ke cid drakṣyanti puruṣāḥ kva cit "
                   "nāryaś cāvidhavā nityaṃ bhaviṣyanti pativratāḥ",
    "R_1,001.073": "na vātajaṃ bhayaṃ kiṃ cin nāpsu majjanti jantavaḥ "
                   "na cāgrijaṃ bhayaṃ kiṃ cid yathā kṛtayuge tathā",
    "R_1,001.074": "aśvamedhaśatair iṣṭvā tathā bahusuvarṇakaiḥ "
                   "gavāṃ koṭyayutaṃ dattvā vidvadbhyo vidhipūrvakam",
    "R_1,001.075": "rājavaṃśāñ śataguṇān sthāpayiṣyati rāghavaḥ "
                   "cāturvarṇyaṃ ca loke 'smin sve sve dharme niyokṣyati",
    "R_1,001.076": "daśavarṣasahasrāṇi daśavarṣaśatāni ca "
                   "rāmo rājyam upāsitvā brahmalokaṃ gamiṣyati",
    "R_1,001.077": "idaṃ pavitraṃ pāpaghnaṃ puṇyaṃ vedaiś ca saṃmitam "
                   "yaḥ paṭhed rāmacaritaṃ sarvapāpaiḥ pramucyate",
    "R_1,001.078": "etad ākhyānam āyuṣyaṃ paṭhan rāmāyaṇaṃ naraḥ "
                   "saputrapautraḥ sagaṇaḥ pretya svarge mahīyate",
    "R_1,001.079": "paṭhan dvijo vāgṛṣabhatvam īyāt syāt kṣatriyo bhūmipatitvam īyāt "
                   "vaṇigjanaḥ paṇyaphalatvam īyāj janaś ca śūdro 'pi mahattvam īyāt",
}


def parasavarna_normalize(deva):
    """Convert an anusvara sitting directly before a class-stop consonant
    (क/ख/ग/घ, च/छ/ज/झ, ट/ठ/ड/ढ, त/थ/द/ध, प/फ/ब/भ) to that class's own
    nasal letter, matching this project's own established citation
    spelling convention (PROJECT_STATE.md gap #15: SKD/Apte spell the
    guttural nasal explicitly before a class stop, e.g. puNgavaH not
    puMgavaH) -- a direct, deterministic application of vyan-7's own rule
    (अनुस्वारस्य ययि परसवर्णः), not a guess. An anusvara before anything
    else (a semivowel, sibilant, or word-final) is left untouched."""
    classes = {
        "क": "ङ्", "ख": "ङ्", "ग": "ङ्", "घ": "ङ्",
        "च": "ञ्", "छ": "ञ्", "ज": "ञ्", "झ": "ञ्",
        "ट": "ण्", "ठ": "ण्", "ड": "ण्", "ढ": "ण्",
        "त": "न्", "थ": "न्", "द": "न्", "ध": "न्",
        "प": "म्", "फ": "म्", "ब": "म्", "भ": "म्",
    }
    out = []
    for i, ch in enumerate(deva):
        nxt = deva[i + 1] if i + 1 < len(deva) else None
        if ch == "ं" and nxt in classes:
            out.append(classes[nxt])
        else:
            out.append(ch)
    return "".join(out)


def build_output():
    lines = []
    for ref, iast in VERSES.items():
        deva = sanscript.transliterate(iast, sanscript.IAST, sanscript.DEVANAGARI)
        deva = parasavarna_normalize(deva)
        lines.append(f"# {ref}")
        lines.append(deva)
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Build Devanagari word-list input for sandhi_splitter.py "
                     "from Valmiki Ramayana Balakanda Sarga 1."
    )
    parser.add_argument(
        "output", nargs="?",
        help="Path to write the output to. If omitted, prints to stdout.",
    )
    args = parser.parse_args()

    output = build_output()
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
