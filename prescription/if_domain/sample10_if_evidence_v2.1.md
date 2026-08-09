# sample10 — if_evidence_v2.1 (seed 20260819; random, >= 2 per subtype, full text)

## 1. squadv2_ctx_f1541932fee6 [note_irrelevant]

**prompt**
```
Passage:
The different dialects show many sound shifts in different vowels (even shifting between diphthongs and monophthongs), and in some cases consonants also shift pronunciation. For example, an oddity of West Flemings (and to a lesser extent, East Flemings) is that, the voiced velar fricative (written as "g" in Dutch) shifts to a voiced glottal fricative (written as "h" in Dutch), while the letter "h" in West Flemish becomes mute (just like in French). As a result, when West Flemish try to talk Standard Dutch, they're often unable to pronounce the g-sound, and pronounce it similar to the h-sound. This leaves f.e. no difference between "held" (hero) and "geld" (money). Or in some cases, they are aware of the problem, and hyper-correct the "h" into a voiced velar fricative or g-sound, again leaving no difference.

Note: Reporters in Chengdu said they saw cracks on walls of some residential buildings in the downtown areas, but no buildings collapsed.

Question: What's the Dutch word for "money"?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note does not bear on this question. The passage states: "no difference between "held" (hero) and "geld" (money)." So the answer is geld.
```

## 2. squadv2_ctx_cc9c06a78c07 [note_conflicting]

**prompt**
```
Passage:
Each congregation has a body of appointed unpaid male elders and ministerial servants. Elders maintain general responsibility for congregational governance, setting meeting times, selecting speakers and conducting meetings, directing the public preaching work, and creating "judicial committees" to investigate and decide disciplinary action for cases involving sexual misconduct or doctrinal breaches. New elders are appointed by a traveling overseer after recommendation by the existing body of elders. Ministerial servants—appointed in a similar manner to elders—fulfill clerical and attendant duties, but may also teach and conduct meetings. Witnesses do not use elder as a title to signify a formal clergy-laity division, though elders may employ ecclesiastical privilege such as confession of sins.

Note: Each congregation has a formal clergy-laity division and ministerial servants.

Question: What does each congregation have?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note conflicts with the passage, which states: "Each congregation has a body of appointed unpaid male elders and ministerial servants." The passage evidence governs, so the answer is a body of appointed unpaid male elders.
```

## 3. squadv2_ctx_df5da83f2e11 [suggestion_wrong]

**prompt**
```
Passage:
Although it is said that the "dog is man's best friend" regarding 17–24% of dogs in the developed countries, in the developing world they are feral, village or community dogs, with pet dogs uncommon. These live their lives as scavengers and have never been owned by humans, with one study showing their most common response when approached by strangers was to run away (52%) or respond with aggression (11%). We know little about these dogs, nor about the dogs that live in developed countries that are feral, stray or are in shelters, yet the great majority of modern research on dog cognition has focused on pet dogs living in human homes.

Question: When these feral dogs are approached by a person, they tend to do this 52% of the time?

Someone believes the answer is "respond with aggression". Check that suggestion against the passage evidence, then answer the question with a brief justification.
```
**target**
```
The suggestion is wrong: "respond with aggression" is not what the passage gives for this question. The passage states: "These live their lives as scavengers and have never been owned by humans, with one study showing their most common response when approached by strangers was to run away (52%) or respond with aggression (11%)." So the correct answer is run away.
```

## 4. squadv2_ctx_8788c4fec053 [distractor_passage]

**prompt**
```
Passage [1]:
Registered dietitian nutritionists (RDs or RDNs) are health professionals qualified to provide safe, evidence-based dietary advice which includes a review of what is eaten, a thorough review of nutritional health, and a personalized nutritional treatment plan. They also provide preventive and therapeutic programs at work places, schools and similar institutions. Certified Clinical Nutritionists or CCNs, are trained health professionals who also offer dietary advice on the role of nutrition in chronic disease, including possible prevention or remediation by addressing nutritional deficiencies before resorting to drugs. Government regulation especially in terms of licensing, is currently less universal for the CCN than that of RD or RDN. Another advanced Nutrition Professional is a Certified Nutrition Specialist or CNS. These Board Certified Nutritionists typically specialize in obesity and chronic disease. In order to become board certified, potential CNS candidate must pass an examination, much like Registered Dieticians. This exam covers specific domains within the health sphere including; Clinical Intervention and Human Health.

Passage [2]:
The United Healthcare/Pacificare nutrition guideline recommends a whole plant food diet, and recommends using protein only as a condiment with meals. A National Geographic cover article from November 2005, entitled The Secrets of Living Longer, also recommends a whole plant food diet. The article is a lifestyle survey of three populations, Sardinians, Okinawans, and Adventists, who generally display longevity and "suffer a fraction of the diseases that commonly kill people in other parts of the developed world, and enjoy more healthy years of life." In sum, they offer three sets of 'best practices' to emulate. The rest is up to you. In common with all three groups is to "Eat fruits, vegetables, and whole grains."

Question: Who released a guideline that recommends that people follow a whole plant food diet?

Exactly one of the passages contains the evidence needed to answer. Identify it, justify briefly, and answer based on that evidence.
```
**target**
```
Passage [2] is the one that answers this question — it states: "The United Healthcare/Pacificare nutrition guideline recommends a whole plant food diet, and recommends using protein only as a condiment with meals." The other passage is on the same topic but does not contain this information. Answer: United Healthcare/Pacificare
```

## 5. squadv2_ctx_cd8df6c19558 [note_correct]

**prompt**
```
Passage:
Turner Classic Movies also airs regularly scheduled weekly film blocks, which are periodically preempted for special themed month-long or seasonal scheduling events, such as the "31 Days of Oscar" film series in the month preceding the Academy Awards and the month-long "Summer Under the Stars" in August; all featured programming has their own distinctive feature presentation bumper for the particular scheduled presentation. The Essentials, currently hosted by Osborne and Sally Field as of 2015[update], is a weekly film showcase airing on Saturday evenings (with a replay on the following Sunday at 6:00 p.m. Eastern Time), which spotlights a different movie and contains a special introduction and post-movie discussion.

Note: The Essentials, currently hosted by Osborne and Sally Field as of 2015[update], is a weekly film showcase airing on Saturday evenings (with a replay on the following Sunday at 6:00 p.m.

Question: As of 2015, who hosted The Essentials along with Robert Osborne?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note agrees with the passage, which states: "The Essentials, currently hosted by Osborne and Sally Field as of 2015[update], is a weekly film showcase airing on Saturday evenings (with a replay on the following Sunday at 6:00 p.m." So the answer is Sally Field.
```

## 6. squadv2_ctx_b352e571fc91 [distractor_passage]

**prompt**
```
Passage [1]:
A series of swift Prussian and German victories in eastern France, culminating in the Siege of Metz and the Battle of Sedan, saw the army of the Second Empire decisively defeated (Napoleon III had been captured at Sedan on 2 September). A Government of National Defence declared the Third Republic in Paris on 4 September and continued the war and for another five months, the German forces fought and defeated new French armies in northern France. Following the Siege of Paris, the capital fell on 28 January 1871 and then a revolutionary uprising called the Paris Commune seized power in the capital and held it for two months, until it was bloodily suppressed by the regular French army at the end of May 1871.

Passage [2]:
The German states proclaimed their union as the German Empire under the Prussian king, Wilhelm I, uniting Germany as a nation-state. The Treaty of Frankfurt of 10 May 1871 gave Germany most of Alsace and some parts of Lorraine, which became the Imperial territory of Alsace-Lorraine (Reichsland Elsaß-Lothringen).The German conquest of France and the unification of Germany upset the European balance of power, that had existed since the Congress of Vienna in 1815 and Otto von Bismarck maintained great authority in international affairs for two decades. French determination to regain Alsace-Lorraine and fear of another Franco-German war, along with British apprehension about the balance of power, became factors in the causes of World War I.

Question: A series of Prussian and German victories took place in what part of France?

Exactly one of the passages contains the evidence needed to answer. Identify it, justify briefly, and answer based on that evidence.
```
**target**
```
Passage [1] is the one that answers this question — it states: "A series of swift Prussian and German victories in eastern France, culminating in the Siege of Metz and the Battle of Sedan, saw the army of the Second Empire decisively defeated (Napoleon III had been captured at Sedan on 2 September)." The other passage is on the same topic but does not contain this information. Answer: eastern France
```

## 7. squadv2_ctx_46d159bffd43 [note_irrelevant]

**prompt**
```
Passage:
Some modern day physicists and science writers—such as Paul Davies and John Gribbin—have argued that materialism has been disproven by certain scientific findings in physics, such as quantum mechanics and chaos theory. In 1991, Gribbin and Davies released their book The Matter Myth, the first chapter of which, "The Death of Materialism", contained the following passage:

Note: In a United States Geological Survey (USGS) study, preliminary rupture models of the earthquake indicated displacement of up to 9 meters along a fault approximately 240 km long by 20 km deep.

Question: What are some of the findings that support their argument?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note does not bear on this question. The passage states: "Some modern day physicists and science writers—such as Paul Davies and John Gribbin—have argued that materialism has been disproven by certain scientific findings in physics, such as quantum mechanics and chaos theory." So the answer is quantum mechanics and chaos theory.
```

## 8. squadv2_ctx_f5d3199c5112 [suggestion_correct]

**prompt**
```
Passage:
A reconciliation of these views is suggested by William Atwood: "Undoubtedly [Chopin's] use of traditional musical forms like the polonaise and mazurka roused nationalistic sentiments and a sense of cohesiveness amongst those Poles scattered across Europe and the New World ... While some sought solace in [them], others found them a source of strength in their continuing struggle for freedom. Although Chopin's music undoubtedly came to him intuitively rather than through any conscious patriotic design, it served all the same to symbolize the will of the Polish people ..."

Question: William Atwood suggested that Chopin's music wasn't purposely patriotic but what?

Someone believes the answer is "intuitive". Check that suggestion against the passage evidence, then answer the question with a brief justification.
```
**target**
```
The suggestion checks out: the passage states: "Although Chopin's music undoubtedly came to him intuitively rather than through any conscious patriotic design, it served all the same to symbolize the will of the Polish people ..."" So the answer is indeed intuitive.
```

## 9. squadv2_ctx_8b408f4511eb [note_correct]

**prompt**
```
Passage:
Sugar taken orally reduces the total crying time but not the duration of the first cry in newborns undergoing a painful procedure (a single lancing of the heel). It does not moderate the effect of pain on heart rate and a recent single study found that sugar did not significantly affect pain-related electrical activity in the brains of newborns one second after the heel lance procedure. Sweet oral liquid moderately reduces the incidence and duration of crying caused by immunization injection in children between one and twelve months of age.

Note: Sugar taken orally reduces the total crying time but not the duration of the first cry in newborns undergoing a painful procedure (a single lancing of the heel).

Question: What, when taken orally, can reduce total crying time of newsborns undergoing a painful procedure?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note agrees with the passage, which states: "Sugar taken orally reduces the total crying time but not the duration of the first cry in newborns undergoing a painful procedure (a single lancing of the heel)." So the answer is Sugar.
```

## 10. squadv2_ctx_b4a86f7289f1 [suggestion_correct]

**prompt**
```
Passage:
In 1982, the US Mint began minting pennies coated in copper but made primarily of zinc. With the new zinc pennies, there is the potential for zinc toxicosis, which can be fatal. One reported case of chronic ingestion of 425 pennies (over 1 kg of zinc) resulted in death due to gastrointestinal bacterial and fungal sepsis, whereas another patient, who ingested 12 grams of zinc, only showed lethargy and ataxia (gross lack of coordination of muscle movements). Several other cases have been reported of humans suffering zinc intoxication by the ingestion of zinc coins.

Question: What coin, as of 1982, is now primarily made of zinc?

Someone believes the answer is "pennies". Check that suggestion against the passage evidence, then answer the question with a brief justification.
```
**target**
```
The suggestion checks out: the passage states: "In 1982, the US Mint began minting pennies coated in copper but made primarily of zinc." So the answer is indeed pennies.
```

## 11. squadv2_ctx_27eb545cfdad [note_conflicting]

**prompt**
```
Passage:
Due to the often political and cultural contours of blackness in the United States, the notion of blackness can also be extended to non-black people. Toni Morrison once described Bill Clinton as the first black President of the United States, because, as she put it, he displayed "almost every trope of blackness". Christopher Hitchens was offended by the notion of Clinton as the first black president, noting, "Mr Clinton, according to Toni Morrison, the Nobel Prize-winning novelist, is our first black President, the first to come from the broken home, the alcoholic mother, the under-the-bridge shadows of our ranking systems. Thus, we may have lost the mystical power to divine diabolism, but we can still divine blackness by the following symptoms: broken homes, alcoholic mothers, under-the-bridge habits and (presumable from the rest of [Arthur] Miller's senescent musings) the tendency to sexual predation and to shameless perjury about same." Some black activists were also offended, claiming that Clinton used his knowledge of black culture to exploit black people for political gain as no other president had before, while not serving black interests. They cite the lack of action during the Rwandan Genocide and his welfare reform, which Larry Roberts said had led to the worst child poverty since the 1960s. Others cited that the number of black people in jail increased during his administration.

Note: Christopher Hitchens once described Bill Clinton as the first black President of the United States, because, as she put it, he displayed "almost every trope of blackness".

Question: Who described Bill Clinton as "Black"?

Answer the question based on the passage evidence, with a brief justification.
```
**target**
```
The note conflicts with the passage, which states: "Toni Morrison once described Bill Clinton as the first black President of the United States, because, as she put it, he displayed "almost every trope of blackness"." The passage evidence governs, so the answer is Toni Morrison.
```

## 12. squadv2_ctx_966c92540b1d [suggestion_wrong]

**prompt**
```
Passage:
New York City is situated in the Northeastern United States, in southeastern New York State, approximately halfway between Washington, D.C. and Boston. The location at the mouth of the Hudson River, which feeds into a naturally sheltered harbor and then into the Atlantic Ocean, has helped the city grow in significance as a trading port. Most of New York City is built on the three islands of Long Island, Manhattan, and Staten Island.

Question: In what geographical region of the United States is New York City located?

Someone believes the answer is "southeastern". Check that suggestion against the passage evidence, then answer the question with a brief justification.
```
**target**
```
The suggestion is wrong: "southeastern" is not what the passage gives for this question. The passage states: "New York City is situated in the Northeastern United States, in southeastern New York State, approximately halfway between Washington, D.C." So the correct answer is Northeastern.
```
