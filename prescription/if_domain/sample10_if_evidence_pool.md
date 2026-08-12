# sample10 — if_evidence_pool (seed 20260821; random, >= 2 per subtype, full text)

## 1. squadv2_ctx_9824246c0ab1 [note_correct]

**prompt**
```
Passage:
People with prolonged, frequent, or close contact with people with TB are at particularly high risk of becoming infected, with an estimated 22% infection rate. A person with active but untreated tuberculosis may infect 10–15 (or more) other people per year. Transmission should occur from only people with active TB – those with latent infection are not thought to be contagious. The probability of transmission from one person to another depends upon several factors, including the number of infectious droplets expelled by the carrier, the effectiveness of ventilation, the duration of exposure, the virulence of the M. tuberculosis strain, the level of immunity in the uninfected person, and others. The cascade of person-to-person spread can be circumvented by segregating those with active ("overt") TB and putting them on anti-TB drug regimens. After about two weeks of effective treatment, subjects with nonresistant active infections generally do not remain contagious to others. If someone does become infected, it typically takes three to four weeks before the newly infected person becomes infectious enough to transmit the disease to others.

Note: People with prolonged, frequent, or close contact with people with TB are at particularly high risk of becoming infected, with an estimated 22% infection rate.

Question: If you're around someone with active TB, what's the chance you'll contract it expressed as a percentage?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note agrees with the passage, which states: "People with prolonged, frequent, or close contact with people with TB are at particularly high risk of becoming infected, with an estimated 22% infection rate." So the answer is 22%.
```

## 2. squadv2_ctx_abf12e7be5fe [suggestion_correct]

**prompt**
```
Passage:
Like Finnish, Estonian employs the Latin script as the basis for its alphabet, which adds the letters ä, ö, ü, and õ, plus the later additions š and ž. The letters c, q, w, x and y are limited to proper names of foreign origin, and f, z, š, and ž appear in loanwords and foreign names only. Ö and ü are pronounced similarly to their equivalents in Swedish and German. Unlike in standard German but like Finnish and Swedish (when followed by 'r'), Ä is pronounced [æ], as in English mat. The vowels Ä, Ö and Ü are clearly separate phonemes and inherent in Estonian, although the letter shapes come from German. The letter õ denotes /ɤ/, unrounded /o/, or a close-mid back unrounded vowel. It is almost identical to the Bulgarian ъ /ɤ̞/ and the Vietnamese ơ, and is used to transcribe the Russian ы.

Question: From what script does the Estonian language get its alphabet?

Someone believes the answer is "Latin". Check that suggestion against the passage evidence, then answer the question with a brief justification.
```
**target**
```
The suggestion checks out: the passage states: "Like Finnish, Estonian employs the Latin script as the basis for its alphabet, which adds the letters ä, ö, ü, and õ, plus the later additions š and ž." So the answer is indeed Latin.
```

## 3. squadv2_ctx_284f0e576b82 [suggestion_wrong]

**prompt**
```
Passage:
Many organisms (of which humans are prime examples) eat from multiple levels of the food chain and, thus, make this classification problematic. A carnivore may eat both secondary and tertiary consumers, and its prey may itself be difficult to classify for similar reasons. Organisms showing both carnivory and herbivory are known as omnivores. Even herbivores such as the giant panda may supplement their diet with meat. Scavenging of carrion provides a significant part of the diet of some of the most fearsome predators. Carnivorous plants would be very difficult to fit into this classification, producing their own food but also digesting anything that they may trap. Organisms that eat detritivores or parasites would also be difficult to classify by such a scheme.

Question: Dead animals that died as a result of natural causes or non-fatal injuries are called?

Someone believes the answer is "Carnivorous plants". Check that suggestion against the passage evidence, then answer the question with a brief justification.
```
**target**
```
The suggestion is wrong: "Carnivorous plants" is not what the passage gives for this question. The passage states: "Scavenging of carrion provides a significant part of the diet of some of the most fearsome predators." So the correct answer is carrion.
```

## 4. squadv2_ctx_bc7903240141 [suggestion_wrong]

**prompt**
```
Passage:
Barcelona won the treble in the 2014–2015 season, winning La Liga, Copa del Rey and UEFA Champions League titles, and became the first European team to have won the treble twice. On 17 May, the club clinched their 23rd La Liga title after defeating Atlético Madrid. This was Barcelona's seventh La Liga title in the last ten years. On 30 May, the club defeated Athletic Bilbao in the Copa del Rey final at Camp Nou. On 6 June, Barcelona won the UEFA Champions League final with a 3–1 win against Juventus, which completed the treble, the club's second in 6 years. Barcelona's attacking trio of Messi, Suárez and Neymar, dubbed MSN, scored 122 goals in all competitions, the most in a season for an attacking trio in Spanish football history.

Question: What team has won the treble competitions twice?

Someone believes the answer is "La Liga". Check that suggestion against the passage evidence, then answer the question with a brief justification.
```
**target**
```
The suggestion is wrong: "La Liga" is not what the passage gives for this question. The passage states: "Barcelona won the treble in the 2014–2015 season, winning La Liga, Copa del Rey and UEFA Champions League titles, and became the first European team to have won the treble twice." So the correct answer is Barcelona.
```

## 5. squadv2_ctx_ec9443c16a31 [distractor_passage]

**prompt**
```
Passage [1]:
After returning from Egypt, Napoleon engineered a coup in November 1799 and became First Consul of the Republic. Another victory over the Austrians at the Battle of Marengo in 1800 secured his political power. With the Concordat of 1801, Napoleon restored the religious privileges of the Catholic Church while keeping the lands seized by the Revolution. The state continued to nominate the bishops and to control church finances. He extended his political control over France until the Senate declared him Emperor of the French in 1804, launching the French Empire. Intractable differences with the British meant that the French were facing a Third Coalition by 1805. Napoleon shattered this coalition with decisive victories in the Ulm Campaign and a historic triumph at the Battle of Austerlitz, which led to the elimination of the Holy Roman Empire. In October 1805, however, a Franco-Spanish fleet was destroyed at the Battle of Trafalgar, allowing Britain to impose a naval blockade of the French coasts. In retaliation, Napoleon established the Continental System in 1806 to cut off continental trade with Britain. The Fourth Coalition took up arms against him the same year because Prussia became worried about growing French influence on the continent. Napoleon knocked out Prussia at the battles of Jena and Auerstedt, then turned his attention towards the Russians and annihilated them in June 1807 at Friedland, which forced the Russians to accept the Treaties of Tilsit.

Passage [2]:
By 17 May, the main Austrian army under Charles had arrived on the Marchfeld. Charles kept the bulk of his troops several miles away from the river bank in hopes of concentrating them at the point where Napoleon decided to cross. On 21 May, the French made their first major effort to cross the Danube, precipitating the Battle of Aspern-Essling. The Austrians enjoyed a comfortable numerical superiority over the French throughout the battle; on the first day, Charles disposed of 110,000 soldiers against only 31,000 commanded by Napoleon. By the second day, reinforcements had boosted French numbers up to 70,000. The battle was characterized by a vicious back-and-forth struggle for the two villages of Aspern and Essling, the focal points of the French bridgehead. By the end of the fighting, the French had lost Aspern but still controlled Essling. A sustained Austrian artillery bombardment eventually convinced Napoleon to withdraw his forces back onto Lobau Island. Both sides inflicted about 23,000 casualties on each other. It was the first defeat Napoleon suffered in a major set-piece battle, and it caused excitement throughout many parts of Europe because it proved that he could be beaten on the battlefield.

Question: On what date did the main Austrian army arrive at the Marchfield?

Exactly one of the passages contains the evidence needed to answer. Identify it, justify briefly, and answer based on that evidence.
```
**target**
```
Passage [2] is the one that answers this question — it states: "By 17 May, the main Austrian army under Charles had arrived on the Marchfeld." The other passage is on the same topic but does not contain this information. Answer: 17 May
```

## 6. squadv2_ctx_63488e5928ac [note_conflicting]

**prompt**
```
Passage:
With Japanese and Allied forces occupying various parts of the island, over the following six months both sides poured resources into an escalating battle of attrition on land, at sea, and in the sky. Most of the Japanese aircraft based in the South Pacific were redeployed to the defense of Guadalcanal. Many were lost in numerous engagements with the Allied air forces based at Henderson Field as well as carrier based aircraft. Meanwhile, Japanese ground forces launched repeated attacks on heavily defended US positions around Henderson Field, in which they suffered appalling casualties. To sustain these offensives, resupply was carried out by Japanese convoys, termed the "Tokyo Express" by the Allies. The convoys often faced night battles with enemy naval forces in which they expended destroyers that the IJN could ill-afford to lose. Later fleet battles involving heavier ships and even daytime carrier battles resulted in a stretch of water near Guadalcanal becoming known as "Ironbottom Sound" from the multitude of ships sunk on both sides. However, the Allies were much better able to replace these losses. Finally recognizing that the campaign to recapture Henderson Field and secure Guadalcanal had simply become too costly to continue, the Japanese evacuated the island and withdrew in February 1943. In the sixth month war of attrition, the Japanese had lost as a result of failing to commit enough forces in sufficient time.

Note: Most of the Japanese aircraft based in the South Pacific were redeployed to the defense of Henderson Field.

Question: Where were most of the Japanese aircraft in the South Pacific redeployed to defend?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note conflicts with the passage, which states: "Most of the Japanese aircraft based in the South Pacific were redeployed to the defense of Guadalcanal." The passage evidence governs, so the answer is Guadalcanal.
```

## 7. squadv2_ctx_126fd15f26d3 [suggestion_correct]

**prompt**
```
Passage:
Collectively encompassing more than 900 million adherents, or nearly forty percent of Christians worldwide, Protestantism is present on all populated continents.[t] The movement is more divided theologically and ecclesiastically than either Eastern Orthodoxy or Roman Catholicism, lacking both structural unity and central human authority. Some Protestant churches do have a worldwide scope and distribution of membership (notably, the Anglican Communion), while others are confined to a single country, or even are solitary church bodies or congregations (such as the former Prussian Union of churches). Nondenominational, evangelical, independent and other churches are on the rise, and constitute a significant part of Protestant Christianity.

Question: What percentage of Christians are Protestant?

Someone believes the answer is "nearly forty percent". Check that suggestion against the passage evidence, then answer the question with a brief justification.
```
**target**
```
The suggestion checks out: the passage states: "Collectively encompassing more than 900 million adherents, or nearly forty percent of Christians worldwide, Protestantism is present on all populated continents.[t] The movement is more divided theologically and ecclesiastically than either Eastern Orthodoxy or Roman Catholicism, lacking both structural unity and central human authority." So the answer is indeed nearly forty percent.
```

## 8. squadv2_ctx_54f0570cc937 [note_irrelevant]

**prompt**
```
Passage:
Drawing from his own experiences in Scouting, Spielberg helped the Boy Scouts of America develop a merit badge in cinematography in order to help promote filmmaking as a marketable skill. The badge was launched at the 1989 National Scout Jamboree, which Spielberg attended, and where he personally counseled many boys in their work on requirements. That same year, 1989, saw the release of Indiana Jones and the Last Crusade. The opening scene shows a teenage Indiana Jones in scout uniform bearing the rank of a Life Scout. Spielberg stated he made Indiana Jones a Boy Scout in honor of his experience in Scouting. For his career accomplishments, service to others, and dedication to a new merit badge Spielberg was awarded the Distinguished Eagle Scout Award.

Note: North Korea: The event was held in Pyongyang on April 28.

Question: What Boy Scout merit badge did Spielberg help develop?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note does not bear on this question. The passage states: "Drawing from his own experiences in Scouting, Spielberg helped the Boy Scouts of America develop a merit badge in cinematography in order to help promote filmmaking as a marketable skill." So the answer is cinematography.
```

## 9. squadv2_ctx_c5b6081fdaec [distractor_passage]

**prompt**
```
Passage [1]:
Smaller boats and ships typically have machine-guns or fast cannons, which can often be deadly to low-flying aircraft if linked to a radar-directed fire-control system radar-controlled cannon for point defence. Some vessels like Aegis cruisers are as much a threat to aircraft as any land-based air defence system. In general, naval vessels should be treated with respect by aircraft, however the reverse is equally true. Carrier battle groups are especially well defended, as not only do they typically consist of many vessels with heavy air defence armament but they are also able to launch fighter jets for combat air patrol overhead to intercept incoming airborne threats.

Passage [2]:
Anti-aircraft warfare or counter-air defence is defined by NATO as "all measures designed to nullify or reduce the effectiveness of hostile air action." They include ground-and air-based weapon systems, associated sensor systems, command and control arrangements and passive measures (e.g. barrage balloons). It may be used to protect naval, ground, and air forces in any location. However, for most countries the main effort has tended to be 'homeland defence'. NATO refers to airborne air defence as counter-air and naval air defence as anti-aircraft warfare. Missile defence is an extension of air defence as are initiatives to adapt air defence to the task of intercepting any projectile in flight.

Question: What kind of weapons can usually be found on smaller boats and ships?

Exactly one of the passages contains the evidence needed to answer. Identify it, justify briefly, and answer based on that evidence.
```
**target**
```
Passage [1] is the one that answers this question — it states: "Smaller boats and ships typically have machine-guns or fast cannons, which can often be deadly to low-flying aircraft if linked to a radar-directed fire-control system radar-controlled cannon for point defence." The other passage is on the same topic but does not contain this information. Answer: machine-guns or fast cannons
```

## 10. squadv2_ctx_b1edf849ffcb [note_conflicting]

**prompt**
```
Passage:
Plymouth is home to the Marine Biological Association of the United Kingdom (MBA) which conducts research in all areas of the marine sciences. The Plymouth Marine Laboratory is an offshoot of the MBA. Together with the National Marine Aquarium, the Sir Alister Hardy Foundation for Ocean Sciences, Plymouth University's Marine Institute and the Diving Diseases Research Centre, these marine-related organisations form the Plymouth Marine Sciences Partnership. The Plymouth Marine Laboratory, which focuses on global issues of climate change and sustainability. It monitors the effects of ocean acidity on corals and shellfish and reports the results to the UK government. It also cultivates algae that could be used to make biofuels or in the treatment of waste water by using technology such as photo-bioreactors. It works alongside the Boots Group to investigate the use of algae in skin care protects, taking advantage of the chemicals they contain that adapt to protect themselves from the sun.

Note: Plymouth is home to the Marine Institute of the United Kingdom (MBA) which conducts research in all areas of the marine sciences.

Question: What organization known as the MBA is based in Plymouth?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note conflicts with the passage, which states: "Plymouth is home to the Marine Biological Association of the United Kingdom (MBA) which conducts research in all areas of the marine sciences." The passage evidence governs, so the answer is Marine Biological Association.
```

## 11. squadv2_ctx_c14dec99db23 [note_correct]

**prompt**
```
Passage:
The last centuries of philosophy have seen vigorous questions regarding the arguments for God's existence raised by such philosophers as Immanuel Kant, David Hume and Antony Flew, although Kant held that the argument from morality was valid. The theist response has been either to contend, as does Alvin Plantinga, that faith is "properly basic", or to take, as does Richard Swinburne, the evidentialist position. Some theists agree that none of the arguments for God's existence are compelling, but argue that faith is not a product of reason, but requires risk. There would be no risk, they say, if the arguments for God's existence were as solid as the laws of logic, a position summed up by Pascal as "the heart has reasons of which reason does not know." A recent theory using concepts from physics and neurophysiology proposes that God can be conceptualized within the theory of integrative level.

Note: The theist response has been either to contend, as does Alvin Plantinga, that faith is "properly basic", or to take, as does Richard Swinburne, the evidentialist position.

Question: How does Alvin Plantinga describe faith?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note agrees with the passage, which states: "The theist response has been either to contend, as does Alvin Plantinga, that faith is "properly basic", or to take, as does Richard Swinburne, the evidentialist position." So the answer is "properly basic".
```

## 12. squadv2_ctx_61b88b9b0613 [note_irrelevant]

**prompt**
```
Passage:
In 1914, Claridge's Company entered into a joint venture to produce tar-bound macadam, with materials manufactured through a subsidiary company called Clarmac Roads Ltd. Two products resulted, namely Clarmac, and Clarphalte, with the former being manufactured by Clarmac Roads and the latter by Claridge's Patent Asphalte Co., although Clarmac was more widely used.[note 1] However, the First World War impacted financially on the Clarmac Company, which entered into liquidation in 1915. The failure of Clarmac Roads Ltd had a flow-on effect to Claridge's Company, which was itself compulsorily wound up, ceasing operations in 1917, having invested a substantial amount of funds into the new venture, both at the outset, and in a subsequent attempt to save the Clarmac Company.

Note: There are four categories of terra nullius, land that is unclaimed by any state: the small unclaimed territory of Bir Tawil between Egypt and Sudan, Antarctica, the oceans, and celestial bodies such as the Moon or Mars.

Question: Which of Claridge's two tar macadams was the more successful?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note does not bear on this question. The passage states: "Two products resulted, namely Clarmac, and Clarphalte, with the former being manufactured by Clarmac Roads and the latter by Claridge's Patent Asphalte Co., although Clarmac was more widely used.[note 1] However, the First World War impacted financially on the Clarmac Company, which entered into liquidation in 1915." So the answer is Clarmac.
```
