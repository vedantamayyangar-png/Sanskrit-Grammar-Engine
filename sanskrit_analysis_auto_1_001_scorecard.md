# Scorecard — local tools vs hand analysis, Bāla Kāṇḍa Sarga 1 

| Measure | Result |
|---|---|
| Junction sandhi between printed tokens, all junctions | 698/708 = 98.6% |
| — real sandhi correctly named (recall) | 291/301 = 96.7% |
| — sandhi reported where there is none | 0 |
| — right junction, wrong sandhi class | 2 |
| Words fused inside one printed token (च+एव, सीता+अपि…) split correctly | 35/43 = 81.4% |
| Samāsa detection — recall (gold compounds found) | 146/185 = 78.9% |
| Samāsa detection — precision (flagged words that really are compounds) | 146/162 = 90.1% |
| Samāsa type exactly right (of compounds found) | 116/146 = 79.5% (0 left 'uncertain') |
| Finite verbs recognised | 55/66 = 83.3% (+1 false) |
| Vibhakti+vacana: answered | 600/605 = 99.2% |
| Vibhakti+vacana: correct (of all declined words) | 528/605 = 87.3% |
| Prātipadika/dhātu correct (of all words) | 710/826 = 86.0% (answered 826) |

## Junction confusion (gold class → system class, count)

- visarga-lopa (āḥ) → none: 4
- t→n (anunāsika) → none: 2
- savarṇa-dīrgha → none: 1
- t+h→ddh → jaśtva: 1
- visarga→o+avagraha → none: 1
- savarṇa-dīrgha → t→n (anunāsika): 1

## Disagreements by class

### prātipadika/dhātu wrong (116)

- 6: वचः gold वचस् system वच
- 6: प्रहृष्टः gold हृष् system प्रहृष्ट
- 7: वक्ष्यामि gold वच् system ब्रू
- 9: कम्बुग्रीवः gold कम्बुग्रीव system कम्बुग्रीवा
- 10: महोरस्कः gold महोरस्क system महोरस्कना
- 10: सुशिराः gold सुशिरस् system सुशिर
- 10: सुललाटः gold सुललाट system लट्
- 11: पीनवक्षाः gold पीनवक्षस् system पीनवक्ष
- 12: प्रजानाम् gold प्रजा system प्रज
- 13: रक्षिता gold रक्षितृ system रक्षिता
- 13: परिरक्षिता gold रक्षितृ system परिरक्षित
- 13: निष्ठितः gold स्था system निष्ठित
- 17: सोमवत् gold सोम system सोमवत्
- 20: पूर्वम् gold पूर्वम् system पूर्व
- 20: एनम् gold एतद् system इदम्
- 21: संयतः gold यम् system संयत्
- 22: अनुपालयन् gold पाल् system अनुपालयत्
- 24: सर्वलक्षणसंपन्ना gold सर्वलक्षणसंपन्ना system सर्वलक्षणसम्पन्न
- 24: अनुगता gold गम् system अनुगत
- 25: अनुगतः gold गम् + क्त system अनुगत
- 26: बहूदकाः gold बहूदका system बहूदक
- 27: रममाणाः gold रममाण system रममाय
- 27: देवगन्धर्वसंकाशाः gold देवगन्धर्वसंकाश system देवगन्धर्वसङ्काशस्
- 27: तत्र gold तद् system तत्र
- 28: तदा gold तद् system तदा
- 28: विलपन् gold लप् system विलपत्
- 29: नियुज्यमानः gold युज् + यक् + शानच् system नियुज्यमान
- 30: पुनः gold पुनर् system पुनः
- 30: पुनः gold पुनर् system पुनः
- 30: ततः gold तद् system ततः
- 31: उपस्पृशन् gold स्पृश् system उपस्पृशत्
- 31: रामागमनकाङ्क्षया gold रामागमनकाङ्क्षा system रामागमनकाङ्क्षयृ
- 36: जनस्थाननिवासिनी gold जनस्थाननिवासिनी system जनस्थाननिवासिन्
- 36: विरूपिता gold विरूपिता system विरूपित
- 37: ततः gold तद् system ततः
- 37: शूर्पणखावाक्यात् gold शूर्पणखावाक्य system शूर्पणखावाक्यात्
- 37: उद्युक्तान् gold युज् + क्त system उद्युक्त
- 37: त्रिशिरसम् gold त्रिशिरस् system त्रिशिर
- 38: निहतानि gold हन् + क्त system निहत
- 39: ततः gold तद् system ततः
- 40: वार्यमाणः gold वृ system वार्यमाण
- 40: सुबहुशः gold सुबहु system सुबहुश
- 40: ते gold युष्मद् system तद्
- 41: तदा gold तद् system तदा
- 42: अपवाह्य gold वह् system वाह्
- 42: जहार gold हृ system हा
- 42: जटायुषम् gold जटायुस् system जटायुष
- 43: निहतम् gold हन् + क्त system निहत
- 43: हृताम् gold हृता system हृत्
- 44: ततः gold तद् system ततः
- 44: जटायुषम् gold जटायुस् system जटायुष
- 44: मार्गमाणः gold मार्ग् system मार्गमाण
- 45: विकृतम् gold कृ + क्त system विकृत
- 45: स्वर्गतः gold स्वर्गत system स्वर्ग
- 46: कथयामास gold कथ system कथयामासन्
- 46: धर्मनिपुणाम् gold धर्मनिपुणा system धर्मनिपुण
- 46: महातेजाः gold महातेजस् system महातेजा
- 47: शबर्या gold शबरी system शबरि
- 47: संगतः gold गम् + क्त system सङ्गत
- 48: समागतः gold गम् + क्त system समागत
- 48: शंसत् gold शंस् system शंसत्
- 49: ततः gold तद् system ततः
- 49: तत्र gold तद् system तत्र
- 49: कथयामास gold कथ system कथयामासन्
- 50: प्रतिज्ञातम् gold ज्ञा + क्त system प्रतिज्ञात
- 50: तदा gold तद् system तदा
- 51: संपूर्णम् gold पॄ + क्त system सम्पूर्ण
- 52: पुनः gold पुनर् system पुनः
- 52: जनयन् gold जन् system जनयत्
- 52: तदा gold तद् system तदा
- 53: ततः gold तद् system ततः
- 53: प्रीतमनाः gold प्रीतमनस् system प्रीतमन
- 53: विश्वस्तः gold श्वस् system विश्वस्त
- 53: किष्किन्धाम् gold किष्किन्धा system किष्किन्ध
- 53: तदा gold तद् system तदा
- 54: ततः gold तद् system ततः
- 54: हरिवरः gold हरिवर system धरिवरय
- 55: ततः gold तद् system ततः
- 55: हत्वा gold हन् system धन्
- 55: तत् gold तत् system तद्
- 55: प्रत्यपादयत् gold पद् system अद्
- 57: ततः gold तद् system ततः
- 57: बली gold बलिन् system बली
- 58: तत्र gold तद् system तत्र
- 58: रावणपालिताम् gold रावणपालिता system रावणपालित
- 58: गताम् gold गता system गत
- 59: निवेद्य gold विद् + णिच् system विद्
- 60: सेनाग्रगान् gold सेनाग्रग system सेनाग्रगत्
- 60: मन्त्रिसुतान् gold मन्त्रिसुत system मन्त्रिसुतत्
- 61: मर्षयन् gold मृष् system मर्षयत्
- 61: यन्त्रिणः gold यन्त्रिन् system यन्त्रिण
- 62: ततः gold तद् system ततः
- 62: आयात् gold या system आय
- 63: दृष्टा gold दृष्टा system दृष्टिन्
- 63: तत्त्वतः gold तत्त्व system तत्त्वत
- 64: ततः gold तद् system ततः
- 65: दर्शयामास gold दृश् + णिच् system दृश्
- 65: सेतुम् gold सेतु system सि
- 68: तदा gold तद् system तदा
- 69: समुत्थाप्य gold स्था + णिच् system समुत्थाप्य
- 69: तदा gold तद् system तदा
- 70: अवाप्तवान् gold आप् + क्तवतु system अवाप्तवत्
- 71: निरामयः gold निरामय system निरायमु
- 72: क्व gold किम् system क्व
- 72: भविष्यन्ति gold भू system अस्
- 73: अप्सु gold अप् system नाप्सु
- 73: मज्जन्ति gold मस्ज् system मज्जत्
- 76: उपासित्वा gold आस् system अस्
- 77: संमितम् gold मा system संमित
- 77: प्रमुच्यते gold मुच् system प्रमुच्यत
- 78: प्रेत्य gold इ system प्रेत्य
- 78: महीयते gold महीङ् system महीयत
- 79: ईयात् gold इ system ईय
- 79: ईयात् gold इ system ईय
- 79: ईयात् gold इ system ईय
- 79: ईयात् gold इ system ईय

### vibhakti/vacana wrong (72)

- 5: एतत् gold (2, 'e') system nominative/singular
- 5: परम् gold (1, 'e') system accusative/singular
- 5: कौतूहलम् gold (1, 'e') system accusative/singular
- 6: वचः gold (2, 'e') system nominative/singular
- 6: प्रहृष्टः gold (1, 'e') system genitive/singular
- 7: कीर्तिताः gold (1, 'b') system instrumental/singular
- 9: कम्बुग्रीवः gold (1, 'e') system genitive/singular
- 10: महोरस्कः gold (1, 'e') system genitive/singular
- 10: सुशिराः gold (1, 'e') system nominative/plural
- 11: पीनवक्षाः gold (1, 'e') system instrumental/singular
- 13: रक्षिता gold (1, 'e') system instrumental/singular
- 13: परिरक्षिता gold (1, 'e') system instrumental/singular
- 16: सर्वगुणोपेतः gold (1, 'e') system genitive/singular
- 21: संयतः gold (1, 'e') system genitive/singular
- 24: सर्वलक्षणसंपन्ना gold (1, 'e') system instrumental/singular
- 24: अनुगता gold (1, 'e') system instrumental/singular
- 26: बहूदकाः gold (2, 'b') system nominative/plural
- 27: रममाणाः gold (1, 'b') system instrumental/singular
- 27: देवगन्धर्वसंकाशाः gold (1, 'b') system nominative/singular
- 29: रामपादप्रसादकः gold (1, 'e') system genitive/singular
- 30: पादुके gold (2, 'd') system nominative/dual
- 31: रामपादौ gold (2, 'd') system nominative/dual
- 31: रामागमनकाङ्क्षया gold (3, 'e') system nominative/singular
- 34: तूणी gold (2, 'd') system nominative/singular
- 36: जनस्थाननिवासिनी gold (1, 'e') system nominative/dual
- 36: विरूपिता gold (1, 'e') system instrumental/singular
- 37: शूर्पणखावाक्यात् gold (5, 'e') system nominative/singular
- 38: चतुर्दश gold (1, 'b') system nominative/singular
- 40: वार्यमाणः gold (1, 'e') system genitive/singular
- 40: ते gold (6, 'e') system nominative/plural
- 41: तत् gold (2, 'e') system nominative/singular
- 41: कालचोदितः gold (1, 'e') system genitive/singular
- 42: नृपात्मजौ gold (2, 'd') system nominative/dual
- 43: हृताम् gold (2, 'e') system genitive/plural
- 44: मार्गमाणः gold (1, 'e') system genitive/singular
- 46: धर्मनिपुणाम् gold (2, 'e') system genitive/plural
- 48: तत् gold (2, 'e') system nominative/singular
- 48: सर्वम् gold (2, 'e') system nominative/singular
- 49: वालिनः gold (6, 'e') system nominative/singular
- 50: प्रतिज्ञातम् gold (1, 'e') system accusative/singular
- 53: प्रीतमनाः gold (1, 'e') system nominative/plural
- 53: किष्किन्धाम् gold (2, 'e') system genitive/plural
- 54: हरिवरः gold (1, 'e') system genitive/singular
- 56: दिशः gold (2, 'b') system nominative/plural
- 58: रावणपालिताम् gold (2, 'e') system genitive/plural
- 58: गताम् gold (2, 'e') system genitive/plural
- 60: पञ्च gold (2, 'b') system nominative/plural
- 60: सेनाग्रगान् gold (2, 'b') system nominative/singular
- 60: सप्त gold (2, 'b') system nominative/plural
- 60: मन्त्रिसुतान् gold (2, 'b') system nominative/singular
- 61: यन्त्रिणः gold (2, 'b') system nominative/singular
- 63: दृष्टा gold (1, 'e') system instrumental/singular
- 67: त्रैलोक्यम् gold (1, 'e') system accusative/singular
- 67: सचराचरम् gold (1, 'e') system accusative/singular
- 67: सदेवर्षिगणम् gold (1, 'e') system accusative/singular
- 67: तुष्टम् gold (1, 'e') system accusative/singular
- 67: महात्मनः gold (6, 'e') system nominative/plural
- 69: देवताभ्यः gold (5, 'b') system dative/plural
- 69: तत् gold (2, 'e') system nominative/singular
- 71: निरामयः gold (1, 'e') system vocative/singular
- 71: दुर्भिक्षभयवर्जितः gold (1, 'e') system genitive/singular
- 73: वातजम् gold (1, 'e') system accusative/singular
- 73: भयम् gold (1, 'e') system accusative/singular
- 73: अप्सु gold (7, 'b') system nominative/singular
- 73: भयम् gold (1, 'e') system accusative/singular
- 76: दशवर्षसहस्राणि gold (2, 'b') system nominative/plural
- 76: दशवर्षशतानि gold (2, 'b') system nominative/plural
- 77: पवित्रम् gold (1, 'e') system accusative/singular
- 77: पापघ्नम् gold (1, 'e') system accusative/singular
- 77: पुण्यम् gold (1, 'e') system accusative/singular
- 77: संमितम् gold (1, 'e') system accusative/singular
- 78: एतत् gold (2, 'e') system nominative/singular

### samāsa missed (39)

- 2: सत्यवाक्यः — सत्यं वाक्यं यस्य सः = सत्यवाक्यः (बहुव्रीहिः)
- 10: सुललाटः — शोभनं ललाटं यस्य सः = सुललाटः (बहुव्रीहिः)
- 11: विशालाक्षः — विशाले अक्षिणी यस्य सः = विशालाक्षः (बहुव्रीहिः)
- 12: सत्यसंधः — सत्या संधा (प्रतिज्ञा) यस्य सः = सत्यसंधः (बहुव्रीहिः)
- 18: धनदेन — धनं ददाति इति धनदः (उपपदतत्पुरुषः — कुबेरः)
- 18: एवंगुणसंपन्नम् — एवं (एवंविधाः) गुणाः = एवंगुणाः (कर्मधारयः); एवंगुणैः संपन्नः = एवंगुणसंपन्नः (त
- 19: यौवराज्येन — युवा चासौ राजा = युवराजः (कर्मधारयः; राजाहःसखिभ्यष्टच्); तस्य भावः = यौवराज्यम् 
- 27: देवगन्धर्वसंकाशाः — देवाश्च गन्धर्वाश्च = देवगन्धर्वाः (इतरेतरद्वन्द्वः); देवगन्धर्वैः संकाशाः (तुल्
- 29: द्विजैः — द्विः जायते इति द्विजः (उपपदतत्पुरुषः)
- 31: रामागमनकाङ्क्षया — रामस्य आगमनम् = रामागमनम् (षष्ठीतत्पुरुषः); रामागमनस्य काङ्क्षा = रामागमनकाङ्क्ष
- 36: शूर्पणखा — शूर्पाणि इव नखाः यस्याः सा = शूर्पणखा (बहुव्रीहिः)
- 36: कामरूपिणी — कामं (यथेष्टं) रूपं धारयति इति कामरूपिणी (उपपदतत्पुरुषः)
- 38: पदानुगान् — पदम् अनुगच्छन्ति इति पदानुगाः (उपपदतत्पुरुषः)
- 39: क्रोधमूर्छितः — क्रोधेन मूर्छितः = क्रोधमूर्छितः (तृतीयातत्पुरुषः)
- 41: अनादृत्य — न आदृत्य = अनादृत्य (नञ्तत्पुरुषः; तस्मान्नुडचि)
- 42: नृपात्मजौ — आत्मनः जातः = आत्मजः (उपपदतत्पुरुषः); नृपस्य आत्मजौ = नृपात्मजौ (षष्ठीतत्पुरुषः)
- 45: स्वर्गतः — स्वर्गं गतः = स्वर्गतः (द्वितीयातत्पुरुषः — द्वितीया श्रितातीतपतितगतात्यस्तप्राप
- 46: महातेजाः — महत् तेजः यस्य सः = महातेजाः (बहुव्रीहिः)
- 47: दशरथात्मजः — दशरथस्य आत्मजः = दशरथात्मजः (षष्ठीतत्पुरुषः)
- 48: सुग्रीवेण — शोभना ग्रीवा यस्य सः = सुग्रीवः (बहुव्रीहिः)
- 49: वैरानुकथनम् — वैरस्य अनुकथनम् = वैरानुकथनम् (षष्ठीतत्पुरुषः)
- 51: प्रत्ययार्थम् — प्रत्ययाय इदम् = प्रत्ययार्थम् (चतुर्थीतत्पुरुषः — अर्थेन नित्यसमासो विशेष्यलिङ्
- 51: पादाङ्गुष्ठेन — पादस्य अङ्गुष्ठः = पादाङ्गुष्ठः (षष्ठीतत्पुरुषः)
- 60: सेनाग्रगान् — सेनायाः अग्रम् = सेनाग्रम् (षष्ठीतत्पुरुषः); सेनाग्रे गच्छन्ति इति सेनाग्रगाः (उ
- 60: मन्त्रिसुतान् — मन्त्रिणां सुताः = मन्त्रिसुताः (षष्ठीतत्पुरुषः)
- 63: प्रदक्षिणम् — प्रगतः दक्षिणम् = प्रदक्षिणः (प्रादितत्पुरुषः)
- 68: विज्वरः — विगतः ज्वरः (सन्तापः) यस्य सः = विज्वरः (प्रादिबहुव्रीहिः)
- 70: अनघः — न विद्यते अघं यस्य सः = अनघः (नञ्बहुव्रीहिः)
- 71: निरामयः — निर्गतः आमयः यस्मात् सः = निरामयः (प्रादिबहुव्रीहिः)
- 72: पतिव्रताः — पतिः एव व्रतं यासां ताः = पतिव्रताः (बहुव्रीहिः)
- 73: वातजम् — वातात् जातम् = वातजम् (उपपदतत्पुरुषः — पञ्चम्यामजातौ)
- 74: कोट्ययुतम् — कोटीनाम् अयुतम् = कोट्ययुतम् (षष्ठीतत्पुरुषः)
- 75: चातुर्वर्ण्यम् — चत्वारः वर्णाः = चतुर्वर्णम् (समाहारद्विगुः) → स्वार्थे ष्यञ्
- 78: रामायणम् — रामस्य अयनम् (चरितम्) = रामायणम् (षष्ठीतत्पुरुषः)
- 78: सगणः — गणेन सह वर्तमानः = सगणः (बहुव्रीहिः)
- 79: द्विजः — द्विः जायते इति द्विजः (उपपदतत्पुरुषः)
- 79: वागृषभत्वम् — वाचाम् ऋषभः (श्रेष्ठः) = वागृषभः (षष्ठीतत्पुरुषः); तस्य भावः = वागृषभत्वम् (तद्ध
- 79: वणिग्जनः — वणिक् चासौ जनः = वणिग्जनः (कर्मधारयः)
- 79: पण्यफलत्वम् — पण्यस्य फलम् = पण्यफलम् (षष्ठीतत्पुरुषः); तस्य भावः = पण्यफलत्वम् (तद्धितः)

### samāsa invented (word is not a compound) (16)

- 7: दुर्लभाः → दुर् + लभ
- 26: भरद्वाजस्य → भर + द्वाज
- 27: आवसथम् → अ + वसथ
- 27: रममाणाः → रम + माय
- 33: शरभङ्गम् → शर + भङ्ग
- 33: सुतीक्ष्णम् → सु + तीक्ष्ण
- 40: सुबहुशः → सु + बहुश
- 42: जटायुषम् → जट + आयुष
- 44: जटायुषम् → जट + आयुष
- 47: शबर्या → शप् + अरि
- 55: आहवे → अ + हव
- 61: आत्मानम् → अ + त्मन्
- 66: आहवे → अ + हव
- 69: नन्दिग्रामम् → नन्दि + ग्राम
- 70: नन्दिग्रामे → नन्दि + ग्राम
- 78: महीयते → मही + यत

### finite verb not recognised (11)

- 46: कथयामास (कथ (कथ वाक्यप्रबन्धे, चुरादिः) + णिच्)
- 48: शंसत् (शंस् (शंसुँ स्तुतौ, भ्वादिः))
- 49: कथयामास (कथ (चुरादिः) + णिच्)
- 62: आयात् (या (या प्रापणे, अदादिः))
- 73: मज्जन्ति (मस्ज् (टुमस्जोँ शुद्धौ, तुदादिः))
- 77: प्रमुच्यते (मुच् (मुचॢँ मोक्षणे, तुदादिः))
- 78: महीयते (महीङ् (पूजायाम्, कण्ड्वादिः))
- 79: ईयात् (इ (इण् गतौ, अदादिः))
- 79: ईयात् (इ (इण् गतौ))
- 79: ईयात् (इ (इण् गतौ))
- 79: ईयात् (इ (इण् गतौ))

### segmentation (word fused inside one printed token) (8)

- 15: सदैकप्रियदर्शनः → gold सदा + एकप्रियदर्शनः; system not split
- 33: चाप्य् → gold च + अपि; system not split
- 35: वधायासुररक्षसाम् → gold वधाय + असुररक्षसाम्; system not split
- 41: तस्याश्रमपदं → gold तस्य + आश्रमपदम्; system tasya + aśramapadam
- 43: विललापाकुलेन्द्रियः → gold विललाप + आकुलेन्द्रियः; system not split
- 61: अस्त्रेणोन्मुहम् → gold अस्त्रेण + उन्मुक्तम्; system not split
- 73: चिन् → gold चित् + न; system not split
- 73: चाग्रिजं → gold च + अग्निजम्; system not split

### samāsa type wrong — gold बहुव्रीहिः / system तत्पुरुषः (7)

- 8: नियतात्मा अ + त्मन्
- 14: अदीनात्मा अ + त्मन्
- 53: प्रीतमनाः प्री + तमन
- 63: महात्मानम् अ + त्मन्
- 63: अमेयात्मा अ + त्मन्
- 71: अरोगः अ + रोग
- 74: विधिपूर्वकम् विधि + पूर्वक

### samāsa type wrong — gold बहुव्रीहिः / system कर्मधारयः (6)

- 10: सुशिराः सु + शिर
- 11: पीनवक्षाः पीन + वक्ष
- 26: बहूदकाः बहु + उदक
- 26: चित्रकूटम् चित्र + कूट
- 28: चित्रकूटम् चित्र + कूट
- 74: बहुसुवर्णकैः बहु + सुवर्णक

### vibhakti not identified (5)

- 10: सुललाटः (gold (1, 'e'))
- 45: स्वर्गतः (gold (1, 'e'))
- 65: सेतुम् (gold (2, 'e'))
- 73: किम् (gold (1, 'e'))
- 73: किम् (gold (1, 'e'))

### samāsa type wrong — gold कर्मधारयः / system तत्पुरुषः (5)

- 21: धर्मपाशेन धर्म + पाश
- 25: शृङ्गवेरपुरे शृङ्ग + वेर + पुर
- 31: नन्दिग्रामे नन्दि + ग्राम
- 54: हेमपिङ्गलः हेम + पिङ्गल
- 57: लवणार्णवम् लवण + अर्णव

### junction sandhi missed — visarga-lopa (āḥ) (4)

- 7: कीर्तिता ⟶ कीर्तिताः + गुणाः → कीर्तिता गुणाः: ससजुषो रुः → भोभगोअघोअपूर्वस्य योऽशि → हलि सर्वेषाम् (
- 11: पीनवक्षा ⟶ पीनवक्षाः + विशालाक्षः → पीनवक्षा विशालाक्षः: ससजुषो रुः → भोभगोअघोअपूर्वस्य योऽशि → हलि स
- 27: रममाणा ⟶ रममाणाः + वने → रममाणा वने: ससजुषो रुः → भोभगोअघोअपूर्वस्य योऽशि → हलि सर्वेषाम् (आः → आ)
- 72: चाविधवा ⟶ अविधवाः + नित्यम् → अविधवा नित्यम्: ससजुषो रुः → भोभगोअघोअपूर्वस्य योऽशि → हलि सर्वेषाम् (

### samāsa type wrong — gold तत्पुरुषः / system बहुव्रीहिः (3)

- 9: शत्रुनिबर्हणः शत्रु + निबर्हण
- 31: रामपादौ राम + पाद
- 71: सुधार्मिकः सु + धार्मिक

### samāsa type wrong — gold कर्मधारयः / system बहुव्रीहिः (3)

- 19: श्रेष्ठगुणैः श्रेष्ठ + गुण
- 34: परमप्रीतः परम + प्रीत
- 68: परमसंतुष्टैः परम + सन्तुष्ट

### junction sandhi missed — t→n (anunāsika) (2)

- 46: ऽभ्यगच्छन् ⟶ अभि + अगच्छत् → अभ्यगच्छत्: इको यणचि; अभ्यगच्छत् + महातेजाः → अभ्यगच्छन्महातेजाः: यरोऽनुना
- 62: आयान् ⟶ आ + अयात् → आयात्: अकः सवर्णे दीर्घः; आयात् + महाकपिः → आयान्महाकपिः: यरोऽनुनासिकेऽनुनासिक

### samāsa type wrong — gold द्विगुः / system द्वन्द्वः (2)

- 76: दशवर्षसहस्राणि दश + वर्ष + सहस्र
- 76: दशवर्षशतानि दश + वर्ष + शत

### noun wrongly tagged as verb (1)

- 10: सुललाटः

### samāsa type wrong — gold तत्पुरुषः / system कर्मधारयः (1)

- 14: सर्वलोकप्रियः सर्व + लोक + प्रिय

### junction sandhi missed — savarṇa-dīrgha (1)

- 33: च ⟶ च + अगस्त्यभ्रातरम् — सन्धिः न कृतः (आर्षप्रयोगः, छन्दोऽनुरोधात्; लौकिके «चागस्त्य°» — अकः

### samāsa type wrong — gold द्वन्द्वः / system द्विगुः (1)

- 38: चतुर्दश चतुर् + दशन्

### junction sandhi wrong class — gold t+h→ddh / system jaśtva (1)

- 55: सुग्रीववचनाद्

### samāsa type wrong — gold तत्पुरुषः / system द्विगुः (1)

- 57: शतयोजनविस्तीर्णम् शत + योजन + विस्तीर्ण

### samāsa type wrong — gold द्वन्द्वः / system तत्पुरुषः (1)

- 71: प्रहृष्टमुदितः प्रहृष्ट + मुदित

### junction sandhi missed — visarga→o+avagraha (1)

- 71: निरायमो ⟶ निरामयः + अरोगः → निरामयो अरोगः (GRETIL-पाठः «निरायमो», पूर्वरूपाभावः — आर्षः; लौकिके «निर

### junction sandhi wrong class — gold savarṇa-dīrgha / system t→n (anunāsika) (1)

- 73: चिन्
