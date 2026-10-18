# Scorecard — local tools vs hand analysis, Bāla Kāṇḍa Sarga 1 

| Measure | Result |
|---|---|
| Junction sandhi between printed tokens, all junctions | 698/708 = 98.6% |
| — real sandhi correctly named (recall) | 291/301 = 96.7% |
| — sandhi reported where there is none | 0 |
| — right junction, wrong sandhi class | 2 |
| Words fused inside one printed token (च+एव, सीता+अपि…) split correctly | 37/43 = 86.0% |
| Samāsa detection — recall (gold compounds found) | 147/185 = 79.5% |
| Samāsa detection — precision (flagged words that really are compounds) | 147/167 = 88.0% |
| Samāsa type exactly right (of compounds found) | 121/147 = 82.3% (0 left 'uncertain') |
| Finite verbs recognised | 59/66 = 89.4% (+1 false) |
| Vibhakti+vacana: answered | 599/605 = 99.0% |
| Vibhakti+vacana: correct (of all declined words) | 540/605 = 89.3% |
| Prātipadika/dhātu correct (of all words) | 714/826 = 86.4% (answered 826) |

## Junction confusion (gold class → system class, count)

- visarga-lopa (āḥ) → none: 4
- t→n (anunāsika) → none: 2
- savarṇa-dīrgha → none: 1
- t+h→ddh → jaśtva: 1
- visarga→o+avagraha → none: 1
- savarṇa-dīrgha → t→n (anunāsika): 1

## Disagreements by class

### prātipadika/dhātu wrong (112)

- 5: नरम् gold नर system नृ
- 6: वचः gold वचस् system वच
- 6: प्रहृष्टः gold हृष् system प्रहृष्ट
- 7: वक्ष्यामि gold वच् system ब्रू
- 10: सुललाटः gold सुललाट system लट्
- 11: पीनवक्षाः gold पीनवक्षस् system पीनवक्षु
- 12: प्रजानाम् gold प्रजा system प्रजाना
- 13: परिरक्षिता gold रक्षितृ system परिरक्षितृ
- 13: निष्ठितः gold स्था system निष्ठित
- 17: सोमवत् gold सोम system सोमवत्
- 20: पूर्वम् gold पूर्वम् system पूर्व
- 20: दत्तवरा gold दत्तवरा system दत्तवर
- 20: देवी gold देवी system देविन्
- 20: एनम् gold एतद् system इदम्
- 21: संयतः gold यम् system संयत
- 22: अनुपालयन् gold पाल् system अनुपालयत्
- 22: पितुः gold पितृ system पितु
- 24: सर्वलक्षणसंपन्ना gold सर्वलक्षणसंपन्ना system सर्वलक्षणसम्पन्न
- 24: नारीणाम् gold नारी system नारि
- 24: अनुगता gold गम् system अनुगत
- 25: अनुगतः gold गम् + क्त system अनुगत
- 26: नदीः gold नदी system नदि
- 26: बहूदकाः gold बहूदका system बहूदक
- 27: रममाणाः gold रममाण system रममाय
- 27: तत्र gold तद् system तत्र
- 28: तदा gold तद् system तदा
- 28: विलपन् gold लप् system विलपत्
- 29: नियुज्यमानः gold युज् + यक् + शानच् system नियुज्यमान
- 30: पादुके gold पादुका system पादुकिन्
- 30: पुनः gold पुनर् system पुनः
- 30: पुनः gold पुनर् system पुनः
- 30: ततः gold तद् system ततः
- 31: रामपादौ gold रामपाद system रामपादु
- 31: उपस्पृशन् gold स्पृश् system उपस्पृशत्
- 34: तूणी gold तूणी system तूणिन्
- 36: वसता gold वसत् system वसति
- 36: जनस्थाननिवासिनी gold जनस्थाननिवासिनी system जनस्थाननिवासिन्
- 36: विरूपिता gold विरूपिता system विरूपित
- 37: ततः gold तद् system ततः
- 37: शूर्पणखावाक्यात् gold शूर्पणखावाक्य system शूर्पणखावाक्यात्
- 37: उद्युक्तान् gold युज् + क्त system उद्युक्त
- 38: निहतानि gold हन् + क्त system निहत
- 38: चतुर्दश gold चतुर्दशन् system चतुर्दशा
- 39: ततः gold तद् system ततः
- 40: वार्यमाणः gold वृ system वार्यमाण
- 40: सुबहुशः gold सुबहु system सुबहुशस्
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
- 46: कथयामास gold कथ system कथयामासन्
- 46: श्रमणीम् gold श्रमणी system श्रमणीम्न्
- 46: धर्मनिपुणाम् gold धर्मनिपुणा system धर्मनिपुअक
- 47: संगतः gold गम् + क्त system सङ्ग
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
- 53: विश्वस्तः gold श्वस् system विश्वस्त
- 53: तदा gold तद् system तदा
- 54: ततः gold तद् system ततः
- 54: हरिवरः gold हरिवर system धरिवर
- 54: महता gold महत् system महता
- 55: ततः gold तद् system ततः
- 55: हत्वा gold हन् system धन्
- 55: तत् gold तत् system तद्
- 55: प्रत्यपादयत् gold पद् system अद्
- 57: ततः gold तद् system ततः
- 58: तत्र gold तद् system तत्र
- 58: ध्यायन्तीम् gold ध्यायन्ती system ध्यायन्तीम्न्
- 58: गताम् gold गता system गत्
- 59: निवेद्य gold विद् + णिच् system विद्
- 61: मर्षयन् gold मृष् system मर्षयत्
- 62: ततः gold तद् system ततः
- 62: आयात् gold या system आयत्
- 63: दृष्टा gold दृष्टा system दृष्टिन्
- 64: ततः gold तद् system ततः
- 65: दर्शयामास gold दृश् + णिच् system दृश्
- 65: सेतुम् gold सेतु system सि
- 67: महता gold महत् system महता
- 68: तदा gold तद् system तदा
- 69: समुत्थाप्य gold स्था + णिच् system समुत्थाप्य
- 69: तदा gold तद् system तदा
- 70: अवाप्तवान् gold आप् + क्तवतु system अवाप्तवत्
- 71: निरामयः gold निरामय system निरायमोन्
- 72: क्व gold किम् system क्व
- 72: नार्यः gold नारी system नार्य
- 72: भविष्यन्ति gold भू system अस्
- 73: अप्सु gold अप् system नाभ्
- 73: मज्जन्ति gold मस्ज् system मज्जत्
- 74: विधिपूर्वकम् gold विधिपूर्वक system विधिपूर्वकम्
- 76: उपासित्वा gold आस् system अस्
- 77: संमितम् gold मा system संमित
- 77: प्रमुच्यते gold मुच् system प्रमुच्यत
- 78: सपुत्रपौत्रः gold सपुत्रपौत्र system सपुत्रपौत्रिन्
- 78: प्रेत्य gold इ system प्रेत्य
- 78: महीयते gold महीङ् system महीयत

### vibhakti/vacana wrong (59)

- 5: एतत् gold (2, 'e') system nominative/singular
- 5: परम् gold (1, 'e') system accusative/singular
- 5: कौतूहलम् gold (1, 'e') system accusative/singular
- 6: वचः gold (2, 'e') system nominative/singular
- 7: कीर्तिताः gold (1, 'b') system instrumental/singular
- 12: प्रजानाम् gold (6, 'b') system accusative/singular
- 17: सदृशः gold (1, 'e') system nominative/plural
- 17: कालाग्निसदृशः gold (1, 'e') system nominative/plural
- 20: दत्तवरा gold (1, 'e') system instrumental/singular
- 22: पितुः gold (6, 'e') system nominative/singular
- 24: सर्वलक्षणसंपन्ना gold (1, 'e') system instrumental/singular
- 24: अनुगता gold (1, 'e') system instrumental/singular
- 26: बहूदकाः gold (2, 'b') system nominative/plural
- 27: रममाणाः gold (1, 'b') system instrumental/singular
- 30: पादुके gold (2, 'd') system dative/singular
- 31: रामपादौ gold (2, 'd') system locative/singular
- 34: तूणी gold (2, 'd') system nominative/singular
- 36: वसता gold (3, 'e') system nominative/singular
- 36: जनस्थाननिवासिनी gold (1, 'e') system nominative/dual
- 36: विरूपिता gold (1, 'e') system instrumental/singular
- 37: शूर्पणखावाक्यात् gold (5, 'e') system nominative/singular
- 38: चतुर्दश gold (1, 'b') system vocative/singular
- 40: ते gold (6, 'e') system nominative/plural
- 41: तत् gold (2, 'e') system nominative/singular
- 42: नृपात्मजौ gold (2, 'd') system nominative/dual
- 43: हृताम् gold (2, 'e') system genitive/plural
- 46: श्रमणीम् gold (2, 'e') system nominative/singular
- 46: धर्मनिपुणाम् gold (2, 'e') system genitive/plural
- 48: तत् gold (2, 'e') system nominative/singular
- 48: सर्वम् gold (2, 'e') system nominative/singular
- 49: वालिनः gold (6, 'e') system nominative/plural
- 50: प्रतिज्ञातम् gold (1, 'e') system accusative/singular
- 54: महता gold (3, 'e') system nominative/singular
- 56: दिशः gold (2, 'b') system nominative/plural
- 58: ध्यायन्तीम् gold (2, 'e') system nominative/singular
- 58: गताम् gold (2, 'e') system genitive/plural
- 60: पञ्च gold (2, 'b') system nominative/plural
- 60: सप्त gold (2, 'b') system nominative/plural
- 61: यन्त्रिणः gold (2, 'b') system genitive/singular
- 63: दृष्टा gold (1, 'e') system instrumental/singular
- 67: महता gold (3, 'e') system nominative/singular
- 67: त्रैलोक्यम् gold (1, 'e') system accusative/singular
- 67: सचराचरम् gold (1, 'e') system accusative/singular
- 67: सदेवर्षिगणम् gold (1, 'e') system accusative/singular
- 67: तुष्टम् gold (1, 'e') system accusative/singular
- 69: देवताभ्यः gold (5, 'b') system dative/plural
- 69: तत् gold (2, 'e') system nominative/singular
- 72: नार्यः gold (1, 'b') system nominative/singular
- 73: वातजम् gold (1, 'e') system accusative/singular
- 73: भयम् gold (1, 'e') system accusative/singular
- 73: भयम् gold (1, 'e') system accusative/singular
- 76: दशवर्षसहस्राणि gold (2, 'b') system nominative/plural
- 76: दशवर्षशतानि gold (2, 'b') system nominative/plural
- 77: पवित्रम् gold (1, 'e') system accusative/singular
- 77: पापघ्नम् gold (1, 'e') system accusative/singular
- 77: पुण्यम् gold (1, 'e') system accusative/singular
- 77: संमितम् gold (1, 'e') system accusative/singular
- 78: एतत् gold (2, 'e') system nominative/singular
- 78: सपुत्रपौत्रः gold (1, 'e') system genitive/singular

### samāsa missed (38)

- 1: वाग्विदाम् — वाचं विदन्ति इति वाग्विदः (उपपदतत्पुरुषः)
- 5: महर्षे — महान् चासौ ऋषिः = महर्षिः (कर्मधारयः; आन्महतः समानाधिकरणजातीययोः)
- 5: एवंविधम् — एवं विधा (प्रकारः) यस्य सः = एवंविधः (बहुव्रीहिः)
- 10: महोरस्कः — महत् उरः यस्य सः = महोरस्कः (बहुव्रीहिः)
- 10: आजानुबाहुः — आ जानुभ्याम् = आजानु (अव्ययीभावः); आजानु (लम्बमानौ) बाहू यस्य सः = आजानुबाहुः (ब
- 10: सुललाटः — शोभनं ललाटं यस्य सः = सुललाटः (बहुव्रीहिः)
- 11: विशालाक्षः — विशाले अक्षिणी यस्य सः = विशालाक्षः (बहुव्रीहिः)
- 12: सत्यसंधः — सत्या संधा (प्रतिज्ञा) यस्य सः = सत्यसंधः (बहुव्रीहिः)
- 18: धनदेन — धनं ददाति इति धनदः (उपपदतत्पुरुषः — कुबेरः)
- 18: एवंगुणसंपन्नम् — एवं (एवंविधाः) गुणाः = एवंगुणाः (कर्मधारयः); एवंगुणैः संपन्नः = एवंगुणसंपन्नः (त
- 19: यौवराज्येन — युवा चासौ राजा = युवराजः (कर्मधारयः; राजाहःसखिभ्यष्टच्); तस्य भावः = यौवराज्यम् 
- 29: द्विजैः — द्विः जायते इति द्विजः (उपपदतत्पुरुषः)
- 36: शूर्पणखा — शूर्पाणि इव नखाः यस्याः सा = शूर्पणखा (बहुव्रीहिः)
- 36: कामरूपिणी — कामं (यथेष्टं) रूपं धारयति इति कामरूपिणी (उपपदतत्पुरुषः)
- 41: अनादृत्य — न आदृत्य = अनादृत्य (नञ्तत्पुरुषः; तस्मान्नुडचि)
- 46: धर्मनिपुणाम् — धर्मे निपुणा = धर्मनिपुणा (सप्तमीतत्पुरुषः)
- 47: दशरथात्मजः — दशरथस्य आत्मजः = दशरथात्मजः (षष्ठीतत्पुरुषः)
- 49: वानरराजेन — वानराणां राजा = वानरराजः (षष्ठीतत्पुरुषः; राजाहःसखिभ्यष्टच्)
- 49: वैरानुकथनम् — वैरस्य अनुकथनम् = वैरानुकथनम् (षष्ठीतत्पुरुषः)
- 51: प्रत्ययार्थम् — प्रत्ययाय इदम् = प्रत्ययार्थम् (चतुर्थीतत्पुरुषः — अर्थेन नित्यसमासो विशेष्यलिङ्
- 52: महेषुणा — महान् इषुः = महेषुः (कर्मधारयः; आन्महतः...)
- 54: हरिवरः — हरिषु वरः = हरिवरः (सप्तमीतत्पुरुषः)
- 63: प्रदक्षिणम् — प्रगतः दक्षिणम् = प्रदक्षिणः (प्रादितत्पुरुषः)
- 67: सचराचरम् — चराणि च अचराणि च = चराचराणि (द्वन्द्वः); चराचरैः सह वर्तमानम् = सचराचरम् (बहुव्र
- 68: विज्वरः — विगतः ज्वरः (सन्तापः) यस्य सः = विज्वरः (प्रादिबहुव्रीहिः)
- 70: अनघः — न विद्यते अघं यस्य सः = अनघः (नञ्बहुव्रीहिः)
- 71: निरामयः — निर्गतः आमयः यस्मात् सः = निरामयः (प्रादिबहुव्रीहिः)
- 72: पतिव्रताः — पतिः एव व्रतं यासां ताः = पतिव्रताः (बहुव्रीहिः)
- 73: वातजम् — वातात् जातम् = वातजम् (उपपदतत्पुरुषः — पञ्चम्यामजातौ)
- 74: कोट्ययुतम् — कोटीनाम् अयुतम् = कोट्ययुतम् (षष्ठीतत्पुरुषः)
- 74: विधिपूर्वकम् — विधिः पूर्वः यस्मिन् कर्मणि तत् = विधिपूर्वकम् (बहुव्रीहिः; शेषाद्विभाषा — कप्)
- 75: चातुर्वर्ण्यम् — चत्वारः वर्णाः = चतुर्वर्णम् (समाहारद्विगुः) → स्वार्थे ष्यञ्
- 78: रामायणम् — रामस्य अयनम् (चरितम्) = रामायणम् (षष्ठीतत्पुरुषः)
- 78: सगणः — गणेन सह वर्तमानः = सगणः (बहुव्रीहिः)
- 79: द्विजः — द्विः जायते इति द्विजः (उपपदतत्पुरुषः)
- 79: वागृषभत्वम् — वाचाम् ऋषभः (श्रेष्ठः) = वागृषभः (षष्ठीतत्पुरुषः); तस्य भावः = वागृषभत्वम् (तद्ध
- 79: भूमिपतित्वम् — भूमेः पतिः = भूमिपतिः (षष्ठीतत्पुरुषः); तस्य भावः = भूमिपतित्वम् (तद्धितः)
- 79: वणिग्जनः — वणिक् चासौ जनः = वणिग्जनः (कर्मधारयः)

### samāsa invented (word is not a compound) (20)

- 26: भरद्वाजस्य → भर + द्वाज
- 27: आवसथम् → अ + वसथ
- 27: रममाणाः → रम + माय
- 33: शरभङ्गम् → शर + भङ्ग
- 33: सुतीक्ष्णम् → सु + तीक्ष्ण
- 42: जटायुषम् → जट + आयुष
- 44: जटायुषम् → जट + आयुष
- 44: मार्गमाणः → मार्ग + माण
- 48: सुग्रीवाय → सु + ग्रीव
- 50: सुग्रीवः → सु + ग्रीव
- 54: सुग्रीवः → सु + ग्रीव
- 55: आहवे → अ + हव
- 55: सुग्रीवम् → सु + ग्रीव
- 61: आत्मानम् → अ + त्मन्
- 66: आहवे → अ + हव
- 69: समुत्थाप्य → समुत्थ + अप्य
- 69: नन्दिग्रामम् → नन्दि + ग्राम
- 70: नन्दिग्रामे → नन्दि + ग्राम
- 75: नियोक्ष्यति → उक्ष् + यतिन्
- 78: महीयते → मही + यत

### samāsa type wrong — gold बहुव्रीहिः / system कर्मधारयः (8)

- 11: पीनवक्षाः पीन + वक्षु
- 20: दत्तवरा दत्त + वर
- 26: बहूदकाः बहु + उदक
- 26: चित्रकूटम् चित्र + कूट
- 28: चित्रकूटम् चित्र + कूट
- 67: महात्मनः मह + आत्मन्
- 68: कृतकृत्यः कृत + कृत्य
- 74: बहुसुवर्णकैः बहु + सुवर्णक

### finite verb not recognised (7)

- 46: कथयामास (कथ (कथ वाक्यप्रबन्धे, चुरादिः) + णिच्)
- 48: शंसत् (शंस् (शंसुँ स्तुतौ, भ्वादिः))
- 49: कथयामास (कथ (चुरादिः) + णिच्)
- 62: आयात् (या (या प्रापणे, अदादिः))
- 73: मज्जन्ति (मस्ज् (टुमस्जोँ शुद्धौ, तुदादिः))
- 77: प्रमुच्यते (मुच् (मुचॢँ मोक्षणे, तुदादिः))
- 78: महीयते (महीङ् (पूजायाम्, कण्ड्वादिः))

### segmentation (word fused inside one printed token) (6)

- 3: चैकप्रियदर्शनः → gold च + एकप्रियदर्शनः; system ca + aikapriyadarśanaḥ
- 15: सदैकप्रियदर्शनः → gold सदा + एकप्रियदर्शनः; system not split
- 33: चाप्य् → gold च + अपि; system not split
- 61: अस्त्रेणोन्मुहम् → gold अस्त्रेण + उन्मुक्तम्; system astreṇa + unmuham
- 73: चिन् → gold चित् + न; system not split
- 73: चाग्रिजं → gold च + अग्निजम्; system not split

### vibhakti not identified (6)

- 10: सुललाटः (gold (1, 'e'))
- 47: संगतः (gold (1, 'e'))
- 65: सेतुम् (gold (2, 'e'))
- 73: किम् (gold (1, 'e'))
- 73: किम् (gold (1, 'e'))
- 74: विधिपूर्वकम् (gold (2, 'e'))

### samāsa type wrong — gold कर्मधारयः / system तत्पुरुषः (6)

- 21: धर्मपाशेन धर्म + पाश
- 25: शृङ्गवेरपुरे शृङ्गवेर + पुर
- 31: नन्दिग्रामे नन्दि + ग्राम
- 54: हेमपिङ्गलः हेम + पिङ्गल
- 57: लवणार्णवम् लवण + अर्णव
- 77: सर्वपापैः सर्वपा + आप

### junction sandhi missed — visarga-lopa (āḥ) (4)

- 7: कीर्तिता ⟶ कीर्तिताः + गुणाः → कीर्तिता गुणाः: ससजुषो रुः → भोभगोअघोअपूर्वस्य योऽशि → हलि सर्वेषाम् (
- 11: पीनवक्षा ⟶ पीनवक्षाः + विशालाक्षः → पीनवक्षा विशालाक्षः: ससजुषो रुः → भोभगोअघोअपूर्वस्य योऽशि → हलि स
- 27: रममाणा ⟶ रममाणाः + वने → रममाणा वने: ससजुषो रुः → भोभगोअघोअपूर्वस्य योऽशि → हलि सर्वेषाम् (आः → आ)
- 72: चाविधवा ⟶ अविधवाः + नित्यम् → अविधवा नित्यम्: ससजुषो रुः → भोभगोअघोअपूर्वस्य योऽशि → हलि सर्वेषाम् (

### samāsa type wrong — gold बहुव्रीहिः / system तत्पुरुषः (3)

- 18: सत्यपराक्रमम् सत्यपर + आक्रम
- 67: सदेवर्षिगणम् सदेव + ऋषिगण
- 71: अरोगः अ + रोग

### samāsa type wrong — gold कर्मधारयः / system बहुव्रीहिः (3)

- 19: श्रेष्ठगुणैः श्रेष्ठ + गुण
- 21: सत्यवचनात् सत्य + वचन
- 68: परमसंतुष्टैः परम + सन्तुष्ट

### junction sandhi missed — t→n (anunāsika) (2)

- 46: ऽभ्यगच्छन् ⟶ अभि + अगच्छत् → अभ्यगच्छत्: इको यणचि; अभ्यगच्छत् + महातेजाः → अभ्यगच्छन्महातेजाः: यरोऽनुना
- 62: आयान् ⟶ आ + अयात् → आयात्: अकः सवर्णे दीर्घः; आयात् + महाकपिः → आयान्महाकपिः: यरोऽनुनासिकेऽनुनासिक

### samāsa type wrong — gold तत्पुरुषः / system कर्मधारयः (2)

- 60: सेनाग्रगान् सेन + अग्रग
- 71: सुधार्मिकः सु + धार्मिक

### samāsa type wrong — gold तत्पुरुषः / system बहुव्रीहिः (1)

- 6: त्रिलोकज्ञः त्रि + लोकज्ञ

### noun wrongly tagged as verb (1)

- 10: सुललाटः

### junction sandhi missed — savarṇa-dīrgha (1)

- 33: च ⟶ च + अगस्त्यभ्रातरम् — सन्धिः न कृतः (आर्षप्रयोगः, छन्दोऽनुरोधात्; लौकिके «चागस्त्य°» — अकः

### samāsa type wrong — gold द्वन्द्वः / system बहुव्रीहिः (1)

- 38: चतुर्दश चतुर् + दशा

### samāsa type wrong — gold द्विगुः / system बहुव्रीहिः (1)

- 51: दशयोजनम् दश + योजन

### junction sandhi wrong class — gold t+h→ddh / system jaśtva (1)

- 55: सुग्रीववचनाद्

### samāsa type wrong — gold द्वन्द्वः / system तत्पुरुषः (1)

- 71: प्रहृष्टमुदितः प्रहृष्ट + मुदित

### junction sandhi missed — visarga→o+avagraha (1)

- 71: निरायमो ⟶ निरामयः + अरोगः → निरामयो अरोगः (GRETIL-पाठः «निरायमो», पूर्वरूपाभावः — आर्षः; लौकिके «निर

### junction sandhi wrong class — gold savarṇa-dīrgha / system t→n (anunāsika) (1)

- 73: चिन्
