# sample10 — if_format_pool (seed 20260819; random, >= 3 per subtype, full text)

## 1. squadv2_ctx_0a828c435844 [extract_A1]

**prompt**
```
Passage:
Program execution might be likened to reading a book. While a person will normally read each word and line in sequence, they may at times jump back to an earlier place in the text or skip sections that are not of interest. Similarly, a computer may sometimes go back and repeat the instructions in some section of the program over and over again until some internal condition is met. This is called the flow of control within the program and it is what allows the computer to perform tasks repeatedly without human intervention.

Question: When a computer goes back and repeats instructions of a program over until an internal condition is met is called what?

Return your answer as a JSON object with exactly this form:
{"answer": "<exact answer span from the passage>"}
Output the JSON object only.
```
**target**
```
{"answer": "the flow of control"}
```

## 2. squadv2_ctx_da1fe192585d [extract_A2]

**prompt**
```
Passage:
At the concluding Treaty of Utrecht, Philip renounced his and his descendants' right to the French throne and Spain lost its empire in Europe. The British Empire was territorially enlarged: from France, Britain gained Newfoundland and Acadia, and from Spain, Gibraltar and Minorca. Gibraltar became a critical naval base and allowed Britain to control the Atlantic entry and exit point to the Mediterranean. Spain also ceded the rights to the lucrative asiento (permission to sell slaves in Spanish America) to Britain.

Question: King Philip renounced his right to the throne after what treaty?

Return your answer as a JSON object with exactly this form:
{"answer": "<exact answer span from the passage>", "evidence_span": "<the passage sentence that contains the answer>"}
Output the JSON object only.
```
**target**
```
{"answer": "Treaty of Utrecht", "evidence_span": "At the concluding Treaty of Utrecht, Philip renounced his and his descendants' right to the French throne and Spain lost its empire in Europe."}
```

## 3. agnews_train_118628 [classify_A4]

**prompt**
```
News article:
J&J takes heart from 13bn deal Johnson & Johnson announced a $25.4bn (13.1bn) deal yesterday to buy Guidant Corporation, giving the healthcare company a stake in the fast-growing market for devices that regulate heartbeats.

Classify the article into exactly one category out of: World, Sports, Business, Sci/Tech.

Return your answer as exactly one line of the form:
label: <one of World, Sports, Business, Sci/Tech>
Output that single line only.
```
**target**
```
label: Business
```

## 4. squadv2_ctx_2e2798194e94 [extract_A2]

**prompt**
```
Passage:
Despite the fact that the Cubs had won 89 games, this fallout was decidedly unlovable, as the Cubs traded superstar Sammy Sosa after he had left the season's final game early and then lied about it publicly. Already a controversial figure in the clubhouse after his corked-bat incident, Sammy's actions alienated much of his once strong fan base as well as the few teammates still on good terms with him, (many teammates grew tired of Sosa playing loud salsa music in the locker room) and possibly tarnished his place in Cubs' lore for years to come. The disappointing season also saw fans start to become frustrated with the constant injuries to ace pitchers Mark Prior and Kerry Wood. Additionally, the '04 season led to the departure of popular commentator Steve Stone, who had become increasingly critical of management during broadcasts and was verbally attacked by reliever Kent Mercker. Things were no better in 2005, despite a career year from first baseman Derrek Lee and the emergence of closer Ryan Dempster. The club struggled and suffered more key injuries, only managing to win 79 games after being picked by many to be a serious contender for the N.L. pennant. In 2006, bottom fell out as the Cubs finished 66–96, last in the NL Central.

Question: Who did the Cubs trade after leaving the final game early and lieing about it?

Return your answer as a JSON object with exactly this form:
{"answer": "<exact answer span from the passage>", "evidence_span": "<the passage sentence that contains the answer>"}
Output the JSON object only.
```
**target**
```
{"answer": "Sammy Sosa", "evidence_span": "Despite the fact that the Cubs had won 89 games, this fallout was decidedly unlovable, as the Cubs traded superstar Sammy Sosa after he had left the season's final game early and then lied about it publicly."}
```

## 5. agnews_train_83569 [classify_A4]

**prompt**
```
News article:
Wholesale Interest in Chinese Retailing Philip Ehrmann, whose Gartmore China Opportunities Fund rose 14.7 percent during the past three months, is boosting his investment in Chinese retailers such as Wumart Stores Inc., anticipating that China's will remain the world's fastest-growing economy in 2005.

Classify the article into exactly one category out of: World, Sports, Business, Sci/Tech.

Return your answer as exactly one line of the form:
label: <one of World, Sports, Business, Sci/Tech>
Output that single line only.
```
**target**
```
label: World
```

## 6. squadv2_ctx_73c288ced7c6 [extract_A1]

**prompt**
```
Passage:
This branch of Protestantism is distinguished by belief in the baptism with the Holy Spirit as an experience separate from conversion that enables a Christian to live a Holy Spirit–filled and empowered life. This empowerment includes the use of spiritual gifts such as speaking in tongues and divine healing—two other defining characteristics of Pentecostalism. Because of their commitment to biblical authority, spiritual gifts, and the miraculous, Pentecostals tend to see their movement as reflecting the same kind of spiritual power and teachings that were found in the Apostolic Age of the early church. For this reason, some Pentecostals also use the term Apostolic or Full Gospel to describe their movement.

Question: Give two examples of spiritual gifts.

Return your answer as a JSON object with exactly this form:
{"answer": "<exact answer span from the passage>"}
Output the JSON object only.
```
**target**
```
{"answer": "speaking in tongues and divine healing"}
```

## 7. agnews_train_3461 [classify_A4]

**prompt**
```
News article:
Top security as eight men appear in court on terror charges In a bombproof building, surrounded by police carrying sub-machine guns, the eight men charged with plotting chemical or radioactive attacks in Britain and the United States made their first appearance in court yesterday since their arrest ...

Classify the article into exactly one category out of: World, Sports, Business, Sci/Tech.

Return your answer as exactly one line of the form:
label: <one of World, Sports, Business, Sci/Tech>
Output that single line only.
```
**target**
```
label: World
```

## 8. agnews_train_110515 [classify_A3]

**prompt**
```
News article:
Potential Guidant Merger Could Be Blow for City (Indianapolis-December 8, 2004) - As the City of Indianapolis tries to build an image as a center for the life sciences, one of its premiere biotechnology companies could be leaving.

Classify the article into exactly one category out of: World, Sports, Business, Sci/Tech.

Return your answer as a JSON object with exactly this form:
{"label": "<one of World, Sports, Business, Sci/Tech>"}
Output the JSON object only.
```
**target**
```
{"label": "Business"}
```

## 9. squadv2_ctx_35422418e5ff [extract_A2]

**prompt**
```
Passage:
Carpet-weaving is historically a major traditional profession for the majority of Armenian women, including many Armenian families. Prominent Karabakh carpet weavers there were men too. The oldest extant Armenian carpet from the region, referred to as Artsakh (see also Karabakh carpet) during the medieval era, is from the village of Banants (near Gandzak) and dates to the early 13th century. The first time that the Armenian word for carpet, gorg, was used in historical sources was in a 1242–1243 Armenian inscription on the wall of the Kaptavan Church in Artsakh.

Question: What job do many Armenian women traditionally do?

Return your answer as a JSON object with exactly this form:
{"answer": "<exact answer span from the passage>", "evidence_span": "<the passage sentence that contains the answer>"}
Output the JSON object only.
```
**target**
```
{"answer": "Carpet-weaving", "evidence_span": "Carpet-weaving is historically a major traditional profession for the majority of Armenian women, including many Armenian families."}
```

## 10. agnews_train_36977 [classify_A3]

**prompt**
```
News article:
Iran Says Talks Only Way to Resolve Nuke Standoff TEHRAN (Reuters) - Iran said Thursday dialogue was the only way to resolve an international standoff over the Islamic republic's nuclear program which Washington says is a cover for building atomic weapons.

Classify the article into exactly one category out of: World, Sports, Business, Sci/Tech.

Return your answer as a JSON object with exactly this form:
{"label": "<one of World, Sports, Business, Sci/Tech>"}
Output the JSON object only.
```
**target**
```
{"label": "World"}
```

## 11. agnews_train_115978 [classify_A3]

**prompt**
```
News article:
UK far-right party leader arrested on charge of inciting racial British police have arrested the leader of the far-right British National Party (BNP) Tuesday, accusing him of inciting racial hatred.

Classify the article into exactly one category out of: World, Sports, Business, Sci/Tech.

Return your answer as a JSON object with exactly this form:
{"label": "<one of World, Sports, Business, Sci/Tech>"}
Output the JSON object only.
```
**target**
```
{"label": "World"}
```

## 12. squadv2_ctx_8bf32c155653 [extract_A1]

**prompt**
```
Passage:
Seattle was also the home base of impresario Alexander Pantages who, starting in 1902, opened a number of theaters in the city exhibiting vaudeville acts and silent movies. His activities soon expanded, and the thrifty Greek went on and became one of America's greatest theater and movie tycoons. Between Pantages and his rival John Considine, Seattle was for a while the western United States' vaudeville mecca. B. Marcus Priteca, the Scottish-born and Seattle-based architect, built several theaters for Pantages, including some in Seattle. The theaters he built for Pantages in Seattle have been either demolished or converted to other uses, but many other theaters survive in other cities of the U.S., often retaining the Pantages name; Seattle's surviving Paramount Theatre, on which he collaborated, was not a Pantages theater.

Question: What type of theater did Alexander Pantages start in Seattle?

Return your answer as a JSON object with exactly this form:
{"answer": "<exact answer span from the passage>"}
Output the JSON object only.
```
**target**
```
{"answer": "vaudeville"}
```
