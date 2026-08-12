# AUDIT_SAMPLES_IF — eval_if_proto.jsonl (seed 20260822; 3 random rows per task_form x condition, full text)

## classification / candidate_keep  (n=50)

### agnews_test_6511  [candidate_contract/candidate_keep]

**prompt**
```
News brief:

Rate hikes by Fed dull ARMs' luster 30-year fixed home loans remain appealing, but variable rates have been on the move up. By Sandra Block. If you're hoping an adjustable-rate mortgage will help you afford your dream house, you may want to rethink those granite countertops.

Drafted desk assignment: Business

Audit the draft. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the desk you stand behind (World, Sports, Business, or Sci/Tech)
```
**reference target**
```
DECISION: KEEP
FINAL: Business
```

### agnews_test_2115  [candidate_contract/candidate_keep]

**prompt**
```
News brief:

Viruses keep on growing Most IT Managers won't question the importance of security, but this priority has been sliding between the third and fourth most important focus for companies.

Drafted desk assignment: Sci/Tech

Audit the draft. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the desk you stand behind (World, Sports, Business, or Sci/Tech)
```
**reference target**
```
DECISION: KEEP
FINAL: Sci/Tech
```

### agnews_test_2362  [candidate_contract/candidate_keep]

**prompt**
```
News brief:

Pascual Rodriguez wins 18th stage of Vuelta race; Heras still ... Spaniard Javier Pascual Rodriguez inched ahead of Colombia's Ivan Parra at the finish line to take the 18th stage of the Spanish Vuelta cycling tour Thursday.

Drafted desk assignment: Sports

Audit the draft. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the desk you stand behind (World, Sports, Business, or Sci/Tech)
```
**reference target**
```
DECISION: KEEP
FINAL: Sports
```

## classification / candidate_revise  (n=50)

### agnews_test_6693  [candidate_contract/candidate_revise]

**prompt**
```
News brief:

FDA Warns Cyberonics on Manufacturing CHICAGO (Reuters) - U.S. regulators warned Cyberonics Inc. <A HREF="http://www.investor.reuters.com/FullQuote.aspx?ticker=CYBX.O target=/stocks/quickinfo/fullquote">CYBX.O of manufacturing deficiencies at the Houston plant that makes its sole product, an implantable device to treat epilepsy, the company said on Monday.

Drafted desk assignment: Sports

Audit the draft. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the desk you stand behind (World, Sports, Business, or Sci/Tech)
```
**reference target**
```
DECISION: REVISE
FINAL: Business
```

### agnews_test_781  [candidate_contract/candidate_revise]

**prompt**
```
News brief:

Facing Arrest, Uma Bharti Quits as Madhya Pradesh Chief BHOPAL (PTI) - Madhya Pradesh Chief Minister Uma Bharti has been forced out of office after four days of political drama as the issue of tainted ministers came back to haunt the Bharatiya Janata Party.

Drafted desk assignment: Business

Audit the draft. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the desk you stand behind (World, Sports, Business, or Sci/Tech)
```
**reference target**
```
DECISION: REVISE
FINAL: World
```

### agnews_test_7138  [candidate_contract/candidate_revise]

**prompt**
```
News brief:

Steelers Look Super The Steelers have all the ingredients to make a run for their fifth Super Bowl title while the NFC trots out its weakest set of challengers in memory.

Drafted desk assignment: Business

Audit the draft. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the desk you stand behind (World, Sports, Business, or Sci/Tech)
```
**reference target**
```
DECISION: REVISE
FINAL: Sports
```

## classification / format_contract  (n=50)

### agnews_test_3031  [format/classify_B4 schema=B4]

**prompt**
```
Here is a news brief:

A's Bullpen Blows Up and Angels Take Title Anaheim scored three runs in the eighth inning off Oakland relievers to rally for a victory and clinch the American League West title.

Which desk should this run under — World, Sports, Business, or Sci/Tech?

Reply with a single line of the exact shape:
category = <World, Sports, Business, or Sci/Tech>
Nothing before or after that line.
```
**reference target**
```
category = Sports
```

### agnews_test_1216  [format/classify_B4 schema=B4]

**prompt**
```
Here is a news brief:

Possible playoff preview A's take a hit in Toronto but come home ... If the playoffs opened right now, instead of next month, the A's would face the Red Sox in the first round -- again. Boston bounced Oakland out of the postseason in five games last year, coming back from a 2-0 deficit to do so.

Which desk should this run under — World, Sports, Business, or Sci/Tech?

Reply with a single line of the exact shape:
category = <World, Sports, Business, or Sci/Tech>
Nothing before or after that line.
```
**reference target**
```
category = Sports
```

### agnews_test_434  [format/classify_B4 schema=B4]

**prompt**
```
Here is a news brief:

Seattle Times business columnist admits plagiarism, resigns A business columnist has resigned from the Seattle Times after admitting he plagiarized the work of other journalists, said the newspaper.

Which desk should this run under — World, Sports, Business, or Sci/Tech?

Reply with a single line of the exact shape:
category = <World, Sports, Business, or Sci/Tech>
Nothing before or after that line.
```
**reference target**
```
category = Business
```

## classification / original  (n=50)

### agnews_test_4965  [classification/cls_plain]

**prompt**
```
Here is a news brief:

Spimming for Dollars Today's new word, for all you dictionary freaks, is "spim". Spam IM (Instant Messaging) = Spim. IM Spam. And for many IM companies it is the bane of their existence requiring increasingly aggressive filtering and block list capabilities.

Which desk should this run under — World, Sports, Business, or Sci/Tech? Answer in one short sentence.
```
**reference target**
```
This one goes under the Sci/Tech desk.
```

### agnews_test_6854  [classification/cls_plain]

**prompt**
```
Here is a news brief:

EU force takes over in Bosnia A European Union force yesterday took over peacekeeping in Bosnia from Nato for an operation seen as a test of the EU's military aspirations and credibility.

Which desk should this run under — World, Sports, Business, or Sci/Tech? Answer in one short sentence.
```
**reference target**
```
This one goes under the World desk.
```

### agnews_test_3431  [classification/cls_plain]

**prompt**
```
Here is a news brief:

Kenyan tree planter wins peace prize Wangari Maathai, a Kenyan environmentalist, today became the first African woman to win the Nobel peace prize. Ms Maathai, 64, Kenya's deputy environment minister, heads the Green Belt movement, a group that

Which desk should this run under — World, Sports, Business, or Sci/Tech? Answer in one short sentence.
```
**reference target**
```
This one goes under the World desk.
```

## constraint / answer_prefix  (n=50)

### squadv2dev_ctx_21f5ab8f6581  [constraint/answer_prefix]

**prompt**
```
Context:
The French Protestant Church of London was established by Royal Charter in 1550. It is now located at Soho Square. Huguenot refugees flocked to Shoreditch, London. They established a major weaving industry in and around Spitalfields (see Petticoat Lane and the Tenterground) in East London. In Wandsworth, their gardening skills benefited the Battersea market gardens. The Old Truman Brewery, then known as the Black Eagle Brewery, was founded in 1724. The flight of Huguenot refugees from Tours, France drew off most of the workers of its great silk mills which they had built.[citation needed] Some of these immigrants moved to Norwich, which had accommodated an earlier settlement of Walloon weavers. The French added to the existing immigrant population, then comprising about a third of the population of the city.

Q: What early Huguenot Church was established in England?

Your whole reply must be a single line that starts with 'ANSWER: ' followed by the answer, and nothing else.
```
**reference target**
```
ANSWER: The French Protestant Church of London
```

### squadv2dev_ctx_acac40b5e924  [constraint/answer_prefix]

**prompt**
```
Context:
Former IPCC chairman Robert Watson has said "The mistakes all appear to have gone in the direction of making it seem like climate change is more serious by overstating the impact. That is worrying. The IPCC needs to look at this trend in the errors and ask why it happened". Martin Parry, a climate expert who had been co-chair of the IPCC working group II, said that "What began with a single unfortunate error over Himalayan glaciers has become a clamour without substance" and the IPCC had investigated the other alleged mistakes, which were "generally unfounded and also marginal to the assessment".

Q: What was Robert Watson's role in the IPCC?

Your whole reply must be a single line that starts with 'ANSWER: ' followed by the answer, and nothing else.
```
**reference target**
```
ANSWER: IPCC chairman
```

### squadv2dev_ctx_ada6bff2fc63  [constraint/answer_prefix]

**prompt**
```
Context:
In 1939, c. 1,300,000 people lived in Warsaw, but in 1945 – only 420,000. During the first years after the war, the population growth was c. 6%, so shortly the city started to suffer from the lack of flats and of areas for new houses. The first remedial measure was the Warsaw area enlargement (1951) – but the city authorities were still forced to introduce residency registration limitations: only the spouses and children of the permanent residents as well as some persons of public importance (like renowned specialists) were allowed to get the registration, hence halving the population growth in the following years. It also bolstered some kind of conviction among Poles that Varsovians thought of themselves as better only because they lived in the capital. Unfortunately this belief still lives on in Poland (although not as much as it used to be) – even though since 1990 there are no limitations to residency registration anymore.

Q: What conviction did many Poles have regarding how the Varsovians thought of themselves?

Your whole reply must be a single line that starts with 'ANSWER: ' followed by the answer, and nothing else.
```
**reference target**
```
ANSWER: as better
```

## constraint / uppercase  (n=50)

### squadv2dev_ctx_dba4b9678717  [constraint/uppercase]

**prompt**
```
Context:
As northwest Europe slowly began to warm up from 22,000 years ago onward, frozen subsoil and expanded alpine glaciers began to thaw and fall-winter snow covers melted in spring. Much of the discharge was routed to the Rhine and its downstream extension. Rapid warming and changes of vegetation, to open forest, began about 13,000 BP. By 9000 BP, Europe was fully forested. With globally shrinking ice-cover, ocean water levels rose and the English Channel and North Sea re-inundated. Meltwater, adding to the ocean and land subsidence, drowned the former coasts of Europe transgressionally.

Q: When did Europe slowly begin to warm up from the last Ice Age?

Reply with just the answer, written entirely in capital letters.
```
**reference target**
```
22,000 YEARS AGO
```

### squadv2dev_ctx_dec62610d02f  [constraint/uppercase]

**prompt**
```
Context:
A number of Huguenots served as mayors in Dublin, Cork, Youghal and Waterford in the 17th and 18th centuries. Numerous signs of Huguenot presence can still be seen with names still in use, and with areas of the main towns and cities named after the people who settled there. Examples include the Huguenot District and French Church Street in Cork City; and D'Olier Street in Dublin, named after a High Sheriff and one of the founders of the Bank of Ireland. A French church in Portarlington dates back to 1696, and was built to serve the significant new Huguenot community in the town. At the time, they constituted the majority of the townspeople.

Q: What Irish cities had Huguenot mayors in the 1600s and 1700s?

Reply with just the answer, written entirely in capital letters.
```
**reference target**
```
DUBLIN, CORK, YOUGHAL AND WATERFORD
```

### squadv2dev_ctx_d59b9f1d37f8  [constraint/uppercase]

**prompt**
```
Context:
Korean economist Hoesung Lee is the chair of the IPCC since October 8, 2015, following the election of the new IPCC Bureau. Before this election, the IPCC was led by his vice-Chair Ismail El Gizouli, who was designated acting Chair after the resignation of Rajendra K. Pachauri in February 2015. The previous chairs were Rajendra K. Pachauri, elected in May 2002; Robert Watson in 1997; and Bert Bolin in 1988. The chair is assisted by an elected bureau including vice-chairs, working group co-chairs, and a secretariat.

Q: Who is the chair of the IPCC?

Reply with just the answer, written entirely in capital letters.
```
**reference target**
```
HOESUNG LEE
```

## constraint / word_limit  (n=50)

### squadv2dev_ctx_130948d87696  [constraint/word_limit]

**prompt**
```
Context:
In 1749 the British government gave land to the Ohio Company of Virginia for the purpose of developing trade and settlements in the Ohio Country. The grant required that it settle 100 families in the territory, and construct a fort for their protection. But, as the territory was also claimed by Pennsylvania, both colonies began pushing for action to improve their respective claims. In 1750 Christopher Gist, acting on behalf of both Virginia and the company, explored the Ohio territory and opened negotiations with the Indian tribes at Logstown. He completed the 1752 Treaty of Logstown in which the local Indians, through their "Half-King" Tanacharison and an Iroquois representative, agreed to terms that included permission to build a "strong house" at the mouth of the Monongahela River (the site of present-day Pittsburgh, Pennsylvania). By the late 17th century, the Iroquois had pushed many tribes out of the Ohio Valley, and kept it as hunting ground by right of conquest.

Q: Who was given land by British goovernment for development of Ohio Country?

Reply in 6 words or fewer, giving just the answer.
```
**reference target**
```
Ohio Company of Virginia
```

### squadv2dev_ctx_70d431032369  [constraint/word_limit]

**prompt**
```
Context:
This motivates the concept of a problem being hard for a complexity class. A problem X is hard for a class of problems C if every problem in C can be reduced to X. Thus no problem in C is harder than X, since an algorithm for X allows us to solve any problem in C. Of course, the notion of hard problems depends on the type of reduction being used. For complexity classes larger than P, polynomial-time reductions are commonly used. In particular, the set of problems that are hard for NP is the set of NP-hard problems.

Q: The complexity of problems often depends on what?

Reply in 8 words or fewer, giving just the answer.
```
**reference target**
```
the type of reduction being used
```

### squadv2dev_ctx_78f5e7103843  [constraint/word_limit]

**prompt**
```
Context:
Greater London has over 900,000 Muslims, (most of South Asian origins and concentrated in the East London boroughs of Newham, Tower Hamlets and Waltham Forest), and among them are some with a strong Islamist outlook. Their presence, combined with a perceived British policy of allowing them free rein, heightened by exposés such as the 2007 Channel 4 documentary programme Undercover Mosque, has given rise to the term Londonistan. Following the 9/11 attacks, however, Abu Hamza al-Masri, the imam of the Finsbury Park Mosque, was arrested and charged with incitement to terrorism which has caused many Islamists to leave the UK to avoid internment.[citation needed]

Q: How many Muslims are in Greater London?

Reply in 4 words or fewer, giving just the answer.
```
**reference target**
```
over 900,000
```

## extraction / candidate_keep  (n=50)

### squadv2dev_ctx_d243d4e2e82b  [candidate_contract/candidate_keep]

**prompt**
```
Context:
Oxygen toxicity to the lungs and central nervous system can also occur in deep scuba diving and surface supplied diving. Prolonged breathing of an air mixture with an O 2 partial pressure more than 60 kPa can eventually lead to permanent pulmonary fibrosis. Exposure to a O 2 partial pressures greater than 160 kPa (about 1.6 atm) may lead to convulsions (normally fatal for divers). Acute oxygen toxicity (causing seizures, its most feared effect for divers) can occur by breathing an air mixture with 21% O 2 at 66 m or more of depth; the same thing can occur by breathing 100% O 2 at only 6 m.

Q: What health condition can deep sea diving cause?

Drafted reply: "Oxygen toxicity"

Audit the drafted reply against the context. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the answer you stand behind
```
**reference target**
```
DECISION: KEEP
FINAL: Oxygen toxicity
```

### squadv2dev_ctx_06a70a5449ea  [candidate_contract/candidate_keep]

**prompt**
```
Context:
Another important role of the immune system is to identify and eliminate tumors. This is called immune surveillance. The transformed cells of tumors express antigens that are not found on normal cells. To the immune system, these antigens appear foreign, and their presence causes immune cells to attack the transformed tumor cells. The antigens expressed by tumors have several sources; some are derived from oncogenic viruses like human papillomavirus, which causes cervical cancer, while others are the organism's own proteins that occur at low levels in normal cells but reach high levels in tumor cells. One example is an enzyme called tyrosinase that, when expressed at high levels, transforms certain skin cells (e.g. melanocytes) into tumors called melanomas. A third possible source of tumor antigens are proteins normally important for regulating cell growth and survival, that commonly mutate into cancer inducing molecules called oncogenes.

Q: What is the process by which the immune system identifies tumors called?

Drafted reply: "immune surveillance"

Audit the drafted reply against the context. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the answer you stand behind
```
**reference target**
```
DECISION: KEEP
FINAL: immune surveillance
```

### squadv2dev_ctx_a628f7eaff7b  [candidate_contract/candidate_keep]

**prompt**
```
Context:
Victoria (abbreviated as Vic) is a state in the south-east of Australia. Victoria is Australia's most densely populated state and its second-most populous state overall. Most of its population is concentrated in the area surrounding Port Phillip Bay, which includes the metropolitan area of its capital and largest city, Melbourne, which is Australia's second-largest city. Geographically the smallest state on the Australian mainland, Victoria is bordered by Bass Strait and Tasmania to the south,[note 1] New South Wales to the north, the Tasman Sea to the east, and South Australia to the west.

Q: Where in Australia is Victoria located?

Drafted reply: "south-east"

Audit the drafted reply against the context. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the answer you stand behind
```
**reference target**
```
DECISION: KEEP
FINAL: south-east
```

## extraction / candidate_revise  (n=50)

### squadv2dev_ctx_2a32beb044b8  [candidate_contract/candidate_revise]

**prompt**
```
Context:
Other green spaces in the city include the Botanic Garden and the University Library garden. They have extensive botanical collection of rare domestic and foreign plants, while a palm house in the New Orangery displays plants of subtropics from all over the world. Besides, within the city borders, there are also: Pole Mokotowskie (a big park in the northern Mokotów, where was the first horse racetrack and then the airport), Park Ujazdowski (close to the Sejm and John Lennon street), Park of Culture and Rest in Powsin, by the southern city border, Park Skaryszewski by the right Vistula bank, in Praga. The oldest park in Praga, the Praga Park, was established in 1865–1871 and designed by Jan Dobrowolski. In 1927 a zoological garden (Ogród Zoologiczny) was established on the park grounds, and in 1952 a bear run, still open today.

Q: What type of space in Warsaw are the Botanic Garden and University Library garden?

Drafted reply: "New Orangery"

Audit the drafted reply against the context. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the answer you stand behind
```
**reference target**
```
DECISION: REVISE
FINAL: green
```

### squadv2dev_ctx_e1a7ed4b8611  [candidate_contract/candidate_revise]

**prompt**
```
Context:
There have been debates as to whether civil disobedience must necessarily be non-violent. Black's Law Dictionary includes non-violence in its definition of civil disobedience. Christian Bay's encyclopedia article states that civil disobedience requires "carefully chosen and legitimate means," but holds that they do not have to be non-violent. It has been argued that, while both civil disobedience and civil rebellion are justified by appeal to constitutional defects, rebellion is much more destructive; therefore, the defects justifying rebellion must be much more serious than those justifying disobedience, and if one cannot justify civil rebellion, then one cannot justify a civil disobedients' use of force and violence and refusal to submit to arrest. Civil disobedients' refraining from violence is also said to help preserve society's tolerance of civil disobedience.

Q: Cristian Bay's encyclopedia concludes that civil disobedience does not only include what behavior?

Drafted reply: "Black's Law"

Audit the drafted reply against the context. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the answer you stand behind
```
**reference target**
```
DECISION: REVISE
FINAL: non-violence
```

### squadv2dev_ctx_6ebd94df2163  [candidate_contract/candidate_revise]

**prompt**
```
Context:
When a consolidation referendum was held in 1967, voters approved the plan. On October 1, 1968, the governments merged to create the Consolidated City of Jacksonville. Fire, police, health & welfare, recreation, public works, and housing & urban development were all combined under the new government. In honor of the occasion, then-Mayor Hans Tanzler posed with actress Lee Meredith behind a sign marking the new border of the "Bold New City of the South" at Florida 13 and Julington Creek. The Better Jacksonville Plan, promoted as a blueprint for Jacksonville's future and approved by Jacksonville voters in 2000, authorized a half-penny sales tax. This would generate most of the revenue required for the $2.25 billion package of major projects that included road & infrastructure improvements, environmental preservation, targeted economic development and new or improved public facilities.

Q: What was the result of the 1967 referendum?

Drafted reply: "Hans Tanzler"

Audit the drafted reply against the context. Give exactly two lines:
DECISION: KEEP if the draft is right, REVISE if not
FINAL: the answer you stand behind
```
**reference target**
```
DECISION: REVISE
FINAL: voters approved the plan
```

## extraction / format_contract  (n=50)

### squadv2dev_ctx_1e26a85d9c8f  [format/extract_B2 schema=B2]

**prompt**
```
Context:
Consultant pharmacy practice focuses more on medication regimen review (i.e. "cognitive services") than on actual dispensing of drugs. Consultant pharmacists most typically work in nursing homes, but are increasingly branching into other institutions and non-institutional settings. Traditionally consultant pharmacists were usually independent business owners, though in the United States many now work for several large pharmacy management companies (primarily Omnicare, Kindred Healthcare and PharMerica). This trend may be gradually reversing as consultant pharmacists begin to work directly with patients, primarily because many elderly people are now taking numerous medications but continue to live outside of institutional settings. Some community pharmacies employ consultant pharmacists and/or provide consulting services.

Q: What is consultant pharmacy mainly concerned with?

Reply with a single JSON object shaped exactly like:
{"final_answer": "<snippet copied from the context>", "support_quote": "<the context sentence that backs it>"}
Nothing before or after the object.
```
**reference target**
```
{"final_answer": "medication regimen review", "support_quote": "Consultant pharmacy practice focuses more on medication regimen review (i.e."}
```

### squadv2dev_ctx_642903e1e350  [format/extract_B2 schema=B2]

**prompt**
```
Context:
Lake Constance consists of three bodies of water: the Obersee ("upper lake"), the Untersee ("lower lake"), and a connecting stretch of the Rhine, called the Seerhein ("Lake Rhine"). The lake is situated in Germany, Switzerland and Austria near the Alps. Specifically, its shorelines lie in the German states of Bavaria and Baden-Württemberg, the Austrian state of Vorarlberg, and the Swiss cantons of Thurgau and St. Gallen. The Rhine flows into it from the south following the Swiss-Austrian border. It is located at approximately 47°39′N 9°19′E﻿ / ﻿47.650°N 9.317°E﻿ / 47.650; 9.317.

Q: How many bodies of water makes up Lake Constance?

Reply with a single JSON object shaped exactly like:
{"final_answer": "<snippet copied from the context>", "support_quote": "<the context sentence that backs it>"}
Nothing before or after the object.
```
**reference target**
```
{"final_answer": "three", "support_quote": "Lake Constance consists of three bodies of water: the Obersee (\"upper lake\"), the Untersee (\"lower lake\"), and a connecting stretch of the Rhine, called the Seerhein (\"Lake Rhine\")."}
```

### squadv2dev_ctx_95f4162a7961  [format/extract_B2 schema=B2]

**prompt**
```
Context:
A deterministic Turing machine is the most basic Turing machine, which uses a fixed set of rules to determine its future actions. A probabilistic Turing machine is a deterministic Turing machine with an extra supply of random bits. The ability to make probabilistic decisions often helps algorithms solve problems more efficiently. Algorithms that use random bits are called randomized algorithms. A non-deterministic Turing machine is a deterministic Turing machine with an added feature of non-determinism, which allows a Turing machine to have multiple possible future actions from a given state. One way to view non-determinism is that the Turing machine branches into many possible computational paths at each step, and if it solves the problem in any of these branches, it is said to have solved the problem. Clearly, this model is not meant to be a physically realizable model, it is just a theoretically interesting abstract machine that gives rise to particularly interesting complexity classes. For examples, see non-deterministic algorithm.

Q: What is generally considered to be the most basic iteration of a Turing machine?

Reply with a single JSON object shaped exactly like:
{"final_answer": "<snippet copied from the context>", "support_quote": "<the context sentence that backs it>"}
Nothing before or after the object.
```
**reference target**
```
{"final_answer": "A deterministic Turing machine", "support_quote": "A deterministic Turing machine is the most basic Turing machine, which uses a fixed set of rules to determine its future actions."}
```

## extraction / insufficient  (n=50)

### squadv2dev_ctx_04fd7d6d3488  [answerability/unanswerable]

**prompt**
```
Context:
Several commemorative events take place every year. Gatherings of thousands of people on the banks of the Vistula on Midsummer’s Night for a festival called Wianki (Polish for Wreaths) have become a tradition and a yearly event in the programme of cultural events in Warsaw. The festival traces its roots to a peaceful pagan ritual where maidens would float their wreaths of herbs on the water to predict when they would be married, and to whom. By the 19th century this tradition had become a festive event, and it continues today. The city council organize concerts and other events. Each Midsummer’s Eve, apart from the official floating of wreaths, jumping over fires, looking for the fern flower, there are musical performances, dignitaries' speeches, fairs and fireworks by the river bank.

Q: What is the polish word for concerts?

Work strictly from the context above. Reply with the shortest snippet of the context that settles the question; if the context leaves it unsettled, state plainly that it cannot be settled from the context.
```
**reference target**
```
The context does not contain what this question asks for, so it cannot be settled from the context.
```

### squadv2dev_ctx_74bf8cca4b02  [answerability/unanswerable]

**prompt**
```
Context:
To make new legislation, TFEU article 294 defines the "ordinary legislative procedure" that applies for most EU acts. The essence is there are three readings, starting with a Commission proposal, where the Parliament must vote by a majority of all MEPs (not just those present) to block or suggest changes, and the Council must vote by qualified majority to approve changes, but by unanimity to block Commission amendment. Where the different institutions cannot agree at any stage, a "Conciliation Committee" is convened, representing MEPs, ministers and the Commission to try and get agreement on a joint text: if this works, it will be sent back to the Parliament and Council to approve by absolute and qualified majority. This means, legislation can be blocked by a majority in Parliament, a minority in the Council, and a majority in the Commission: it is harder to change EU law than stay the same. A different procedure exists for budgets. For "enhanced cooperation" among a sub-set of at least member states, authorisation must be given by the Council. Member state governments should be informed by the Commission at the outset before any proposals start the legislative procedure. The EU as a whole can only act within its power set out in the Treaties. TEU articles 4 and 5 state that powers remain with the member states unless they have been conferred, although there is a debate about the Kompetenz-Kompetenz question: who ultimately has the "competence" to define the EU's "competence". Many member state courts believe they decide, other member state Parliaments believe they decide, while within the EU, the Court of Justice believes it has the final say.

Q: What does TFEU article not define?

Work strictly from the context above. Reply with the shortest snippet of the context that settles the question; if the context leaves it unsettled, state plainly that it cannot be settled from the context.
```
**reference target**
```
The context does not contain what this question asks for, so it cannot be settled from the context.
```

### squadv2dev_ctx_6d5d37af5c73  [answerability/unanswerable]

**prompt**
```
Context:
While BSkyB had been excluded from being a part of the ONdigital consortium, thereby making them a competitor by default, BSkyB was able to join ITV Digital's free-to-air replacement, Freeview, in which it holds an equal stake with the BBC, ITV, Channel 4 and National Grid Wireless. Prior to October 2005, three BSkyB channels were available on this platform: Sky News, Sky Three, and Sky Sports News. Initially BSkyB provided Sky Travel to the service. However, this was replaced by Sky Three on 31 October 2005, which was itself later re-branded as 'Pick TV' in 2011.

Q: What consortium was BSkyB included with?

Work strictly from the context above. Reply with the shortest snippet of the context that settles the question; if the context leaves it unsettled, state plainly that it cannot be settled from the context.
```
**reference target**
```
The context does not contain what this question asks for, so it cannot be settled from the context.
```

## extraction / original  (n=50)

### squadv2dev_ctx_b8e0b30dcde6  [answerability/answerable]

**prompt**
```
Context:
Virgin Media (re-branded in 2007 from NTL:Telewest) started to offer a high-definition television (HDTV) capable set top box, although from 30 November 2006 until 30 July 2009 it only carried one linear HD channel, BBC HD, after the conclusion of the ITV HD trial. Virgin Media has claimed that other HD channels were "locked up" or otherwise withheld from their platform, although Virgin Media did in fact have an option to carry Channel 4 HD in the future. Nonetheless, the linear channels were not offered, Virgin Media instead concentrating on its Video On Demand service to carry a modest selection of HD content. Virgin Media has nevertheless made a number of statements over the years, suggesting that more linear HD channels are on the way.

Q: When was virgin media rebranded from NTL Telewest?

Work strictly from the context above. Reply with the shortest snippet of the context that settles the question; if the context leaves it unsettled, state plainly that it cannot be settled from the context.
```
**reference target**
```
2007
```

### squadv2dev_ctx_06a70a5449ea  [answerability/answerable]

**prompt**
```
Context:
Another important role of the immune system is to identify and eliminate tumors. This is called immune surveillance. The transformed cells of tumors express antigens that are not found on normal cells. To the immune system, these antigens appear foreign, and their presence causes immune cells to attack the transformed tumor cells. The antigens expressed by tumors have several sources; some are derived from oncogenic viruses like human papillomavirus, which causes cervical cancer, while others are the organism's own proteins that occur at low levels in normal cells but reach high levels in tumor cells. One example is an enzyme called tyrosinase that, when expressed at high levels, transforms certain skin cells (e.g. melanocytes) into tumors called melanomas. A third possible source of tumor antigens are proteins normally important for regulating cell growth and survival, that commonly mutate into cancer inducing molecules called oncogenes.

Q: What is the process by which the immune system identifies tumors called?

Work strictly from the context above. Reply with the shortest snippet of the context that settles the question; if the context leaves it unsettled, state plainly that it cannot be settled from the context.
```
**reference target**
```
immune surveillance
```

### squadv2dev_ctx_3efbb629f5a3  [answerability/answerable]

**prompt**
```
Context:
Harvard has the largest university endowment in the world. As of September 2011[update], it had nearly regained the loss suffered during the 2008 recession. It was worth $32 billion in 2011, up from $28 billion in September 2010 and $26 billion in 2009. It suffered about 30% loss in 2008-09. In December 2008, Harvard announced that its endowment had lost 22% (approximately $8 billion) from July to October 2008, necessitating budget cuts. Later reports suggest the loss was actually more than double that figure, a reduction of nearly 50% of its endowment in the first four months alone. Forbes in March 2009 estimated the loss to be in the range of $12 billion. One of the most visible results of Harvard's attempt to re-balance its budget was their halting of construction of the $1.2 billion Allston Science Complex that had been scheduled to be completed by 2011, resulting in protests from local residents. As of 2012[update], Harvard University had a total financial aid reserve of $159 million for students, and a Pell Grant reserve of $4.093 million available for disbursement.

Q: What was the Harvard endowment total in 2011?

Work strictly from the context above. Reply with the shortest snippet of the context that settles the question; if the context leaves it unsettled, state plainly that it cannot be settled from the context.
```
**reference target**
```
$32 billion
```

## extraction / status_found  (n=50)

### squadv2dev_ctx_c82100776072  [answerability/struct_found]

**prompt**
```
Context:
Fresno has three large public parks, two in the city limits and one in county land to the southwest. Woodward Park, which features the Shinzen Japanese Gardens, numerous picnic areas and several miles of trails, is in North Fresno and is adjacent to the San Joaquin River Parkway. Roeding Park, near Downtown Fresno, is home to the Fresno Chaffee Zoo, and Rotary Storyland and Playland. Kearney Park is the largest of the Fresno region's park system and is home to historic Kearney Mansion and plays host to the annual Civil War Revisited, the largest reenactment of the Civil War in the west coast of the U.S.

You are auditing one entry of a records table. Entry "large_public_parks_fresno" is defined by the question: How many large public parks does Fresno have?

Report back in exactly two lines — first line 'STATUS: OK' when the context supplies the value, otherwise 'STATUS: INSUFFICIENT'; second line 'FINAL_ANSWER: <the value>', writing NULL when it is missing.
```
**reference target**
```
STATUS: OK
FINAL_ANSWER: three
```

### squadv2dev_ctx_4fbce1bcbcb9  [answerability/struct_found]

**prompt**
```
Context:
Past faculty have also included Egyptologist James Henry Breasted, mathematician Alberto Calderón, Nobel prize winning economist and classical liberalism defender Friedrich Hayek, meteorologist Ted Fujita, chemists Glenn T. Seaborg, the developer of the actinide concept and Nobel Prize winner Yuan T. Lee, Nobel Prize winning novelist Saul Bellow, political philosopher and author Allan Bloom, cancer researchers Charles Brenton Huggins and Janet Rowley, astronomer Gerard Kuiper, one of the most important figures in the early development of the discipline of linguistics Edward Sapir, and the founder of McKinsey & Co., James O. McKinsey.

You are auditing one entry of a records table. Entry "egyptologist_also_apart_university" is defined by the question: What Egyptologist was also apart of the university's faculty?

Report back in exactly two lines — first line 'STATUS: OK' when the context supplies the value, otherwise 'STATUS: INSUFFICIENT'; second line 'FINAL_ANSWER: <the value>', writing NULL when it is missing.
```
**reference target**
```
STATUS: OK
FINAL_ANSWER: James Henry Breasted
```

### squadv2dev_ctx_746aa8287dd0  [answerability/struct_found]

**prompt**
```
Context:
The Rhine emerges from Lake Constance, flows generally westward, as the Hochrhein, passes the Rhine Falls, and is joined by its major tributary, the river Aare. The Aare more than doubles the Rhine's water discharge, to an average of nearly 1,000 m3/s (35,000 cu ft/s), and provides more than a fifth of the discharge at the Dutch border. The Aare also contains the waters from the 4,274 m (14,022 ft) summit of Finsteraarhorn, the highest point of the Rhine basin. The Rhine roughly forms the German-Swiss border from Lake Constance with the exceptions of the canton of Schaffhausen and parts of the cantons of Zürich and Basel-Stadt, until it turns north at the so-called Rhine knee at Basel, leaving Switzerland.

You are auditing one entry of a records table. Entry "after_rhine_emerges_lake" is defined by the question: After the Rhine emerges from Lake Constance, what direction does it flow?

Report back in exactly two lines — first line 'STATUS: OK' when the context supplies the value, otherwise 'STATUS: INSUFFICIENT'; second line 'FINAL_ANSWER: <the value>', writing NULL when it is missing.
```
**reference target**
```
STATUS: OK
FINAL_ANSWER: westward
```

## extraction / status_insufficient  (n=50)

### squadv2dev_ctx_eefa3d988576  [answerability/struct_insufficient]

**prompt**
```
Context:
The Rhine (Romansh: Rein, German: Rhein, French: le Rhin, Dutch: Rijn) is a European river that begins in the Swiss canton of Graubünden in the southeastern Swiss Alps, forms part of the Swiss-Austrian, Swiss-Liechtenstein border, Swiss-German and then the Franco-German border, then flows through the Rhineland and eventually empties into the North Sea in the Netherlands. The biggest city on the river Rhine is Cologne, Germany with a population of more than 1,050,000 people. It is the second-longest river in Central and Western Europe (after the Danube), at about 1,230 km (760 mi),[note 2][note 1] with an average discharge of about 2,900 m3/s (100,000 cu ft/s).

You are auditing one entry of a records table. Entry "smallest_nation_rhine_runs" is defined by the question: What is the smallest nation that the Rhine runs through?

Report back in exactly two lines — first line 'STATUS: OK' when the context supplies the value, otherwise 'STATUS: INSUFFICIENT'; second line 'FINAL_ANSWER: <the value>', writing NULL when it is missing.
```
**reference target**
```
STATUS: INSUFFICIENT
FINAL_ANSWER: NULL
```

### squadv2dev_ctx_a4180c8c4fb2  [answerability/struct_insufficient]

**prompt**
```
Context:
Pathogens can rapidly evolve and adapt, and thereby avoid detection and neutralization by the immune system; however, multiple defense mechanisms have also evolved to recognize and neutralize pathogens. Even simple unicellular organisms such as bacteria possess a rudimentary immune system, in the form of enzymes that protect against bacteriophage infections. Other basic immune mechanisms evolved in ancient eukaryotes and remain in their modern descendants, such as plants and invertebrates. These mechanisms include phagocytosis, antimicrobial peptides called defensins, and the complement system. Jawed vertebrates, including humans, have even more sophisticated defense mechanisms, including the ability to adapt over time to recognize specific pathogens more efficiently. Adaptive (or acquired) immunity creates immunological memory after an initial response to a specific pathogen, leading to an enhanced response to subsequent encounters with that same pathogen. This process of acquired immunity is the basis of vaccination.

You are auditing one entry of a records table. Entry "known_adapting_evolving_slowly" is defined by the question: What is known for adapting and evolving slowly?

Report back in exactly two lines — first line 'STATUS: OK' when the context supplies the value, otherwise 'STATUS: INSUFFICIENT'; second line 'FINAL_ANSWER: <the value>', writing NULL when it is missing.
```
**reference target**
```
STATUS: INSUFFICIENT
FINAL_ANSWER: NULL
```

### squadv2dev_ctx_6bc44b640bbe  [answerability/struct_insufficient]

**prompt**
```
Context:
Since September 2004, the official home of the Scottish Parliament has been a new Scottish Parliament Building, in the Holyrood area of Edinburgh. The Scottish Parliament building was designed by Spanish architect Enric Miralles in partnership with local Edinburgh Architecture firm RMJM which was led by Design Principal Tony Kettle. Some of the principal features of the complex include leaf-shaped buildings, a grass-roofed branch merging into adjacent parkland and gabion walls formed from the stones of previous buildings. Throughout the building there are many repeated motifs, such as shapes based on Raeburn's Skating Minister. Crow-stepped gables and the upturned boat skylights of the Garden Lobby, complete the unique architecture. Queen Elizabeth II opened the new building on 9 October 2004.

You are auditing one entry of a records table. Entry "since_1904_home_scottish" is defined by the question: Since 1904, the home of Scottish Parliament has been where?

Report back in exactly two lines — first line 'STATUS: OK' when the context supplies the value, otherwise 'STATUS: INSUFFICIENT'; second line 'FINAL_ANSWER: <the value>', writing NULL when it is missing.
```
**reference target**
```
STATUS: INSUFFICIENT
FINAL_ANSWER: NULL
```

## reading_qa / insufficient  (n=50)

### squadv2dev_ctx_2a6d5ac46464  [reading_qa/rq_insufficient]

**prompt**
```
Reference material:
[1] Newton's Third Law is a result of applying symmetry to situations where forces can be attributed to the presence of different objects. The third law means that all forces are interactions between different bodies,[Note 3] and thus that there is no such thing as a unidirectional force or a force that acts on only one body. Whenever a first body exerts a force F on a second body, the second body exerts a force −F on the first body. F and −F are equal in magnitude and opposite in direction. This law is sometimes referred to as the action-reaction law, with F called the "action" and −F the "reaction". The action and the reaction are simultaneous:

Using the material above, write a brief explanation answering: Newton's Fifth Law is the result of applying symmetry to what?
If the material does not cover what is asked, note that instead of speculating.
```
**reference target**
```
No part of the material covers this question, so it cannot be answered from what is given.
```

### squadv2dev_ctx_52439861694d  [reading_qa/rq_insufficient]

**prompt**
```
Reference material:
[1] Jacksonville is the most populous city in Florida, and the twelfth most populous city in the United States. As of 2010[update], there were 821,784 people and 366,273 households in the city. Jacksonville has the country's tenth-largest Arab population, with a total population of 5,751 according to the 2000 United States Census. Jacksonville has Florida's largest Filipino American community, with 25,033 in the metropolitan area as of the 2010 Census. Much of Jacksonville's Filipino community served in or has ties to the United States Navy.

Using the material above, write a brief explanation answering: In what city or the Arabs the twelve largest ethnic group?
If the material does not cover what is asked, note that instead of speculating.
```
**reference target**
```
No part of the material covers this question, so it cannot be answered from what is given.
```

### squadv2dev_ctx_99733c49bef3  [reading_qa/rq_insufficient]

**prompt**
```
Reference material:
[1] In this equation, a dimensional constant is used to describe the relative strength of gravity. This constant has come to be known as Newton's Universal Gravitation Constant, though its value was unknown in Newton's lifetime. Not until 1798 was Henry Cavendish able to make the first measurement of using a torsion balance; this was widely reported in the press as a measurement of the mass of the Earth since knowing could allow one to solve for the Earth's mass given the above equation. Newton, however, realized that since all celestial bodies followed the same laws of motion, his law of gravity had to be universal. Succinctly stated, Newton's Law of Gravitation states that the force on a spherical object of mass due to the gravitational pull of mass is

Using the material above, write a brief explanation answering: What is used to describe the weakness of gravity?
If the material does not cover what is asked, note that instead of speculating.
```
**reference target**
```
No part of the material covers this question, so it cannot be answered from what is given.
```

## reading_qa / original  (n=50)

### crepe_test_2019_b-01145  [reading_qa/rq_answerable]

**prompt**
```
Reference material:
[1] The cranium dysfunction mechanical changes in the gut can compress the vagus nerve at any number of locations along the vagus, slowing the heart. As the heart slows, autonomic reflexes are triggered to increase blood pressure and heart rate.
[2] In adults the normal resting heart rate ranges from 60 to 90 beats per minute. The resting heart rate in children is much faster. In athletes, however, the resting heart rate can be as slow as 40 beats per minute, and be considered as normal.

Using the material above, write a brief explanation answering: Why does our heart beat *harder* sometimes?
If the material does not cover what is asked, note that instead of speculating.
```
**reference target**
```
Your heart beats to pump oxygenated blood to your body as needed. When you are at rest your heart beats slowly. When you are active your heart beats faster and harder to pump more blood faster through your body. Your lungs provide the oxygen so when you are active you breathe faster and deeper to take in more oxygen
```

### crepe_test_2019_b-07248  [reading_qa/rq_answerable]

**prompt**
```
Reference material:
[1] The speaking dialect or accent of a person may differ greatly from the general singing accent that a person uses while singing. When people sing, they generally use the accent or neutral accent that is used in the style of music they are singing in, rather than a regional accent or dialect; the style of music and the popular center/region of the style has more influence on the singing accent of a person than where they come from. For example, in the English language, British singers of rock or popular music often sing in an American accent or neutral accent instead of an English accent.
[2] "When I started out with rock bands, I sang in an American accent. Then I heard real Americans sing the blues and it made me feel like a fraud. Ever since then, the most important thing for me is to be true to who I am and where I come from."

Using the material above, write a brief explanation answering: why do singers from the UK and Australia sound American when they sing but not when they talk?
If the material does not cover what is asked, note that instead of speculating.
```
**reference target**
```
When you sing you have to enunciate and also change pitch and tone in specific ways. This causes their natural accents to drop off making most people regardless of accent sounds pretty much the same. However when they talk they are speaking naturally which allows their individual accents to show. Edited for content.
```

### crepe_test_2019_b-00800  [reading_qa/rq_answerable]

**prompt**
```
Reference material:
[1] Calculations can be performed to determine the conditions needed for a critical state, mass, geometry, concentration etc. Where fissile materials are handled in civil and military installations, specially trained personnel are employed to carry out such calculations, and to ensure that all reasonably practicable measures are used to prevent criticality accidents, during both planned normal operations and any potential process upset conditions that cannot be dismissed on the basis of negligible likelihoods (reasonably foreseeable accidents).
[2] There are a large number of techniques for containing radioactive materials so that it does not spread beyond the containment and become contamination. In the case of liquids this is by the use of high integrity tanks or containers, usually with a sump system so that leakage can be detected by radiometric or conventional instrumentation.

Using the material above, write a brief explanation answering: What is a geometrically safe container to prevent radioactive materials to reach criticality? I've been reading a lot about nucular accidents and there is often this phrase of a "geometrically safe" container popping up. What is it and how does the geometry of a container prevent criticality?
If the material does not cover what is asked, note that instead of speculating.
```
**reference target**
```
You get chain reactions with nuclear reactions because radioactive material decaying can cause other radioactive material nearby to decay to. In nuclear reactors you want the reaction to be just enough to keep going and give of some heat, but not more. With bombs you want them to really get worse exponentially fast and give of as much energy as possible in a very short time. When transporting stuff you ideally don't want it to explode or even keep heating itself. One way to do this is to keep the mass down.
```

## revision / candidate_keep  (n=50)

### crepe_test_2019_b-06481  [candidate_contract/candidate_keep]

**prompt**
```
Reference material:
[1] Like other forms of TB, XDR-TB is spread through the air. When a person with infectious TB coughs, sneezes, talks or spits, they propel TB germs, known as bacilli, into the air. XDR-TB cannot be spread by kissing, sharing food or drinks and by shaking someone’s hand. The bacterium has the ability to stay in the air for several hours. A person needs only to inhale a small number of these to be infected. People infected with TB bacilli will not necessarily become sick with the disease. The immune system "walls off" the TB bacilli which, protected by a thick waxy coat, can lie dormant for years.
[2] Humans are the only known reservoirs of "M. tuberculosis". A misconception is that "M. tuberculosis" can be spread by shaking hands, making contact with toilet seats, sharing food or drink, sharing toothbrushes, or kissing. It can only be spread through air droplets originating from a person who has the disease either coughing, sneezing, speaking, or singing.

Question: How does TB spread through coughing and talking, but not through kissing?

Drafted response:
TB is spread through the air, and kissing normally doesn't involve breathing on or in the other person.

Audit the drafted response against the material and the question. Give exactly two lines:
DECISION: KEEP if the draft is sound, REVISE if it gets something wrong
FINAL: the response you would send
```
**reference target**
```
DECISION: KEEP
FINAL: TB is spread through the air, and kissing normally doesn't involve breathing on or in the other person.
```

### crepe_test_2019_b-06039  [candidate_contract/candidate_keep]

**prompt**
```
Reference material:
[1] Tennis elbow is the most common elbow problem among athletes, highly associated with world class tennis players, it is a condition that involves the common wrist extensor origin, in particular the origin of extensor carpi radialis. The causes for tennis elbow includes any activity, not only tennis, where the repetitive use of the extensor muscles of the forearm may cause acute or chronic tendonitis of the tensinous insertion of these muscles at the lateral epicondyle of the elbow. The condition itself is most common with painters, plumbers, and carpenters. Further studied have shown that auto-workers, butchers and cooks also get tennis elbow more often than the rest of the population.
[2] At first, racquets were made of wood and the strings were made of animal gut. These were very heavy and did not provide comfortable play, but they were used for more than thirty years until the great player Jose, the “Poison” Becerra revolutionized the sport. Manufacturers that made tennis products started to manufacture parallel products for frontenis when Becerra started to win championships. In the 1990s a Mexican company, “Master Pro”, was created exclusively to manufacture frontenis products. Recently, other companies have appeared specializing in frontenis equipment.

Question: Why do pro tennis players not have one extremely muscular arm?

Drafted response:
Muscles are usually built from weight training, and swinging a tennis racket generally isn't enough to build muscle.

Audit the drafted response against the material and the question. Give exactly two lines:
DECISION: KEEP if the draft is sound, REVISE if it gets something wrong
FINAL: the response you would send
```
**reference target**
```
DECISION: KEEP
FINAL: Muscles are usually built from weight training, and swinging a tennis racket generally isn't enough to build muscle.
```

### crepe_test_2019_b-02065  [candidate_contract/candidate_keep]

**prompt**
```
Reference material:
[1] The switch used to control a 3-way lamp is usually a rotary switch or a pull-chain switch. Although it is referred to as a 3-way switch, it has four positions, off, lamp one (low), lamp two (medium), and lamps one and two (high). When properly connected to a 3-way socket containing a 3-way bulb, this switch will first power one filament, then the other filament, then both, then return to the off position. To do this, the switch must be capable of operating two different circuits. Internal to the switch there are two sets of switch contacts that are not connected electrically, but which are connected mechanically in such a way that they operate together as shown in this table.
[2] Another type of 2-circuit lamp is also fairly common. This is the lamp with night light. While related to a 3-way lamp, this lamp is different from a 3-way lamp in both its intention and the parts it uses. The main intent of a lamp with night light is not to offer three levels of light, but rather to offer only two levels: a bright working light, and a very dim night light or decorative accent. Typically it does still use the 3-way 2-circuit switch. However, instead of having one 3-way socket, it uses two regular sockets.

Question: why do lamps take two clicks to turn on and off?

Drafted response:
Not every lamp is designed to take 2 clicks to activate.

Audit the drafted response against the material and the question. Give exactly two lines:
DECISION: KEEP if the draft is sound, REVISE if it gets something wrong
FINAL: the response you would send
```
**reference target**
```
DECISION: KEEP
FINAL: Not every lamp is designed to take 2 clicks to activate.
```

## revision / candidate_revise  (n=50)

### crepe_test_2019_b-02446  [candidate_contract/candidate_revise]

**prompt**
```
Reference material:
[1] Typically this occurs as a result of a marine transgression or regression, or the progressive development of a delta. As the shoreline advances or retreats, a succession of continuous deposits representing different environments (for example beach, shallow water, deeper water) may be left behind. Although each type of deposit (facies) may be continuous over a wide area, its age varies according to the position of the shoreline through time.
[2] Measuring habitat structure at multiple scales is typical in seascape ecology, particularly where a single meaningful scale is not known or not meaningful to the ecological process of interest. Multi-scale measurements have been used to discover the scale at which populations are associated with key habitat features. With regard to scaling seascapes, one approach is to select spatial and temporal scales to be ecologically meaningful to the organism’s movements or other processes of interest.

Question: If water is homogeneous, why do different beaches from the same body of water have different levels clarity or cleanliness in the water?

Drafted response:
Water is homogenous.

Audit the drafted response against the material and the question. Give exactly two lines:
DECISION: KEEP if the draft is sound, REVISE if it gets something wrong
FINAL: the response you would send
```
**reference target**
```
DECISION: REVISE
FINAL: Water is not homogenous since impurities in one area of a body of water doesn't spread worldwide to all bodies.
```

### crepe_test_2019_b-03022  [candidate_contract/candidate_revise]

**prompt**
```
Reference material:
[1] Modern personal computer motherboards have a backup battery to run the real-time clock circuit and retain configuration memory while the system is turned off. This is often called the CMOS battery or BIOS battery. The original IBM AT through to the PS/2 range, used a relatively large primary lithium battery, compared to later models, to retain the clock and configuration memory. These early machines required the backup battery to be replaced periodically due to the relatively large power consumption. Some manufacturers of clone machines used a rechargeable battery to avoid the problems that could be created by a failing battery. Modern systems use a coin style primary battery. In these later
[2] With current technology, most modern computers keep track of local civil time, as do many other household and personal devices such as VCRs, DVRs, cable TV receivers, PDAs, pagers, cell phones, fax machines, telephone answering machines, cameras, camcorders, central air conditioners, and microwave ovens.

Question: How do computers/smartphones keep tracking the date and hour even when they're disconnected from any energy source?

Drafted response:
When a PC or phone is turned off it has no connection to continue to track the date and hour.

Audit the drafted response against the material and the question. Give exactly two lines:
DECISION: KEEP if the draft is sound, REVISE if it gets something wrong
FINAL: the response you would send
```
**reference target**
```
DECISION: REVISE
FINAL: When a PC or phone is turned off it can still track the time and date by using the CMOS battery implemented into the device.
```

### crepe_test_2019_b-03847  [candidate_contract/candidate_revise]

**prompt**
```
Reference material:
[1] The effects of manipulation and biases are also internal challenges prediction markets need to deal with, i.e. liquidity or other factors not intended to be measured are taken into account as risk factors by the market participants, distorting the market probabilities. Prediction markets may also be subject to speculative bubbles. For example, in the year 2000 IEM presidential futures markets, seeming "inaccuracy" comes from buying that occurred on or after Election Day, 11/7/00, but, by then, the trend was clear.
[2] The former head of the National Bureau of Economic Research said in March 2008 that he believed the country was then in a recession, and it could be a severe one. A number of private economists generally predicted a mild recession ending in the summer of 2008 when the economic stimulus checks going to 130 million households started being spent. A chief economist at Moody's predicted in March 2008 that policymakers would act in a concerted and aggressive way to stabilize the financial markets, and that the economy would suffer, but not enter a prolonged and severe recession. It takes many months before the National Bureau of Economic Research, the unofficial arbiter of when recessions begin a

Question: If a prediction of a recession causes the market to crash, can it be said that the prediction itself is part of the cause of the recession? Like a self-fulfilling prophecy?

Drafted response:
A prediction of a recession will cause the market to crash.

Audit the drafted response against the material and the question. Give exactly two lines:
DECISION: KEEP if the draft is sound, REVISE if it gets something wrong
FINAL: the response you would send
```
**reference target**
```
DECISION: REVISE
FINAL: A prediction of a recession will not cause the market to crash without an additional trigger.
```

## structured_response / format_contract  (n=50)

### agnews_test_5266  [format/classify_B3 schema=B3]

**prompt**
```
Here is a news brief:

Big Tax Plans, Big Tax Risks Reforming the tax system is more politically risky and economically complex than the president let on during the campaign.

Which desk should this run under — World, Sports, Business, or Sci/Tech?

Reply with a single JSON object shaped exactly like:
{"category": "<World, Sports, Business, or Sci/Tech>"}
Nothing before or after the object.
```
**reference target**
```
{"category": "Business"}
```

### squadv2dev_ctx_d4c04f259b4a  [format/extract_B1 schema=B1]

**prompt**
```
Context:
Private schools, also known as independent schools, non-governmental, or nonstate schools, are not administered by local, state or national governments; thus, they retain the right to select their students and are funded in whole or in part by charging their students tuition, rather than relying on mandatory taxation through public (government) funding; at some private schools students may be able to get a scholarship, which makes the cost cheaper, depending on a talent the student may have (e.g. sport scholarship, art scholarship, academic scholarship), financial need, or tax credit scholarships that might be available.

Q: Along with sport and art, what is a type of talent scholarship?

Reply with a single JSON object shaped exactly like:
{"final_answer": "<snippet copied from the context>"}
Nothing before or after the object.
```
**reference target**
```
{"final_answer": "academic"}
```

### agnews_test_3066  [format/classify_B3 schema=B3]

**prompt**
```
Here is a news brief:

AL Wrap: Indians, Twins Split Unique Doubleheader NEW YORK (Reuters) - Ben Broussard belted a two-run homer to give the Cleveland Indians a 5-2 win over the Minnesota Twins to salvage a split of a unique doubleheader on the final day of the regular season on Sunday.

Which desk should this run under — World, Sports, Business, or Sci/Tech?

Reply with a single JSON object shaped exactly like:
{"category": "<World, Sports, Business, or Sci/Tech>"}
Nothing before or after the object.
```
**reference target**
```
{"category": "Sports"}
```
