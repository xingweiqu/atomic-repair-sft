# sample10 — k_revision_2000 (seed 20260820, generator A, 2Wiki train)

## w2ktr_0106987  [fix_similar_entity]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Thomas Morse — Thomas Morse( born June 30, 1968) is an American composer of film and concert music.
(2) Kavalam Chundan (film) — Kavalam Chundan is a 1967 Indian Malayalam film, directed by J. Sasikumar and produced by V. P. M. Manikkam. The film stars Sathyan, Sharada, Adoor Bhasi and P. J. Antony in the lead roles. The film had musical score by G. Devarajan.
(3) Henri Verdun — Henri Verdun( 1895–1977) was a French composer of film scores.
(4) Abe Meyer — Abe Meyer( 1901 – 1969) was an American composer of film scores.
(5) Tarcisio Fusco — Tarcisio Fusco was an Italian composer of film scores. He was the brother of the composer Giovanni Fusco and the uncle of operatic soprano Cecilia Fusco.
(6) Bert Grund — Bert Grund( 1920–1992) was a German composer of film scores.
(7) Amedeo Escobar — Amedeo Escobar( 1888–1973) was an Italian composer of film scores.
(8) Walter Ulfig — Walter Ulfig was a German composer of film scores.
(9) Alonso Mudarra — Alonso Mudarra( c. 1510 – April 1, 1580) was a Spanish composer of the Renaissance, and also played the vihuela, a guitar- shaped string instrument. He was an innovative composer of instrumental music as well as songs, and was the composer of the earliest surviving music for the guitar.
(10) G. Devarajan — Paravoor Govindan Devarajan, popularly known as G. Devarajan or Devarajan master, was an Indian music composer. He is considered one of the greatest music directors in Indian film music arena. He scored music for more than three hundred Malayalam films, many dramas, and twenty Tamil and four Kannada movies. Many of his compositions remain ever green classics in Malayalam. His music in the Tamil film "Annai Velankanni" has received many accolades. Devarajan received Kerala Government's Best Music Director award five times, among other honours. He is regarded as the greatest music composer ever in the history of Malayalam cinema.

Q: What is the place of birth of the composer of film Kavalam Chundan (Film)?

A previous reader answered: "Alonso Mudarra", citing the source "Alonso Mudarra".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is wrong. It picks the wrong entity: the cited source "Alonso Mudarra" is not where this question's answer is established. Based on the source "G. Devarajan": "Paravoor Govindan Devarajan, popularly known as G. Devarajan or Devarajan master, was an Indian music composer." The correct answer is Paravoor.
```

meta: `{"cand": "Alonso Mudarra", "cited_title": "Alonso Mudarra", "hop": "similar_entity", "cand_source": "same_context_title", "cite_sentence": "Paravoor Govindan Devarajan, popularly known as G. Devarajan or Devarajan master, was an Indian music composer."}`

## w2ktr_0112399  [fix_wrong_citation]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Yasuichi Oshima — He is the father of manga artist Towa Oshima.
(2) Obata Toramori — He was the father of Obata Masamori.
(3) Carl-Heinz Schroth — Carl-Heinz Schroth (29 June 1902 – 19 July 1989) was a German actor and film director. He appeared in 60 films between 1931 and 1989. He also directed seven films between 1953 and 1963. He was born in Innsbruck, Austria to Else Ruttersheim and film and stage actor Heinrich Schroth and died in Munich, Germany. His younger half-sister was actress Hannelore Schroth, from his father's marriage to actress Käthe Haack. He was married to the actress Karin Jacobsen.
(4) Lars Eliasson — He is the father of the later Member of Parliament Anna Eliasson.
(5) Reaching for the Moon (1930 film) — Reaching for the Moon is a 1930 American pre-Code black and white musical film. Originally released at 91 minutes; surviving versions are usually cut to 62 minutes. A 74- minute version aired in 1998 on USA cable channel AMC. The DVD version runs just under 72 minutes. The film's working title was" Lucky Break" and is known as" Para alcanzar la Luna" in Spain. It is not to be confused with the Fairbanks silent film" Reaching for the Moon"( 1917).
(6) Inoue Masaru (bureaucrat) — Viscount was the first Director of Railways in Japan and is known as the" father of the Japanese railways".
(7) Peter Hamel — Peter Hamel( 1911–1979) was a German screenwriter and a director of film and television. He appeared as himself in the 1948 comedy" Film Without a Title". He is the father of the composer Peter Michael Hamel.
(8) Reaching for the Stars (film) — Reaching for the Stars  is a 1955 West German drama film directed by Carl-Heinz Schroth and starring Erik Schumann, Liselotte Pulver and Gustav Knuth. The film's sets were designed by the art director Hans Sohnle. It was partly shot in Venice.
(9) Ian Barry (director) — Ian Barry is an Australian director of film and TV.
(10) Paul Brooke — Paul Brooke( born 22 November 1944) is a retired English actor of film, television and radio. He is the father of actor Tom Brooke.

Q: Who is the father of the director of film Reaching For The Stars (Film)?

A previous reader answered: "Cormac mac Airt", citing the source "Reaching for the Stars (film)".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is wrong. The cited source "Reaching for the Stars (film)" does not state that answer; the citation does not support it. Based on the source "Carl-Heinz Schroth": "He was born in Innsbruck, Austria to Else Ruttersheim and film and stage actor Heinrich Schroth and died in Munich, Germany." The correct answer is Heinrich Schroth.
```

meta: `{"cand": "Cormac mac Airt", "cited_title": "Reaching for the Stars (film)", "hop": "wrong_citation", "cand_source": "donor_answer", "cite_sentence": "He was born in Innsbruck, Austria to Else Ruttersheim and film and stage actor Heinrich Schroth and died in Munich, Germany."}`

## w2ktr_0103270  [keep]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Peter Levin — Peter Levin is an American director of film, television and theatre.
(2) Giovannona Long-Thigh — Giovannona Coscialunga disonorata con onore (internationally released as Giovannona Long-Thigh) is a 1973 commedia sexy all'italiana directed by Sergio Martino. The film reteams the two main actors of the 1972 film " Quel gran pezzo dell'Ubalda tutta nuda e tutta calda" and, as with the previous film, it was very successful commercially. The original title reprises Lina Wertmüller's "Mimì metallurgico ferito nell'onore".
(3) Ubalda, All Naked and Warm — Quel gran pezzo dell' Ubalda tutta nuda e tutta calda, internationally released as Ubalda, All Naked and Warm( though translated to Spanish as Ubalda la hermosa, ardiente y fogosa) is a 1972 Italian comedy film directed by Mariano Laurenti. It gained a great commercial success and launched the" commedia sexy all'italiana" genre. Walter Veltroni defined the film a" cult- title" and a title which is" a piece of Italian history". The couple of main actors Edwige Fenech- Pippo Franco was reunited for the similar" Giovannona Long- Thigh", released the following year.
(4) Terence Robinson — Terence D. Robinson( date of birth and death unknown) was a male wrestler who competed for England.
(5) Etan Boritzer — Etan Boritzer( born 1950) is an American writer of children ’s literature who is best known for his book" What is God?" first published in 1989. His best selling" What is?" illustrated children's book series on character education and difficult subjects for children is a popular teaching guide for parents, teachers and child- life professionals. Boritzer gained national critical acclaim after" What is God?" was published in 1989 although the book has caused controversy from religious fundamentalists for its universalist views. The other current books in the" What is?" series include What is Love?, What is Death?, What is Beautiful?, What is Funny?, What is Right?, What is Peace?, What is Money?, What is Dreaming?, What is a Friend?, What is True?, What is a Family?, What is a Feeling?" The series is now also translated into 15 languages. Boritzer was first published in 1963 at the age of 13 when he wrote an essay in his English class at Wade Junior High School in the Bronx, New York on the assassination of John F. Kennedy. His essay was included in a special anthology by New York City public school children compiled and published by the New York City Department of Education. Boritzer now lives in Venice, California and maintains his publishing office there also. He has helped numerous other authors to get published through" How to Get Your Book Published!" programs. Boritzer is also a yoga teacher who teaches regular classes locally and guest- teaches nationally. He is also recognized nationally as an erudite speaker on" The Teachings of the Buddha."
(6) Theodred II (Bishop of Elmham) — Theodred II was a medieval Bishop of Elmham. The date of Theodred's consecration unknown, but the date of his death was sometime between 995 and 997.
(7) Brian Saunders (weightlifter) — Brian Saunders( date of birth and death unknown) was a male weightlifter who competed for England.
(8) Sergio Martino — Sergio Martino (born 19 July 1938) is an Italian film director and producer, notable for his contributions to the giallo genre. Martino is the brother of the late producer Luciano Martino (who died in 2013). They collaborated frequently in their respective professions. Their grandfather was director Gennaro Righelli. Sergio Martino worked for both the big screen as well as for Italian television where he does most of his current work. He often worked with actress Edwige Fenech who in the 1970s was married to his brother Luciano. He also worked with a lot of genre actors such as George Hilton (who was married to Sergio's cousin), Ivan Rassimov and Claudio Cassinelli, as well as famed Italian screenwriter Ernesto Gastaldi. Martino's pseudonyms include: Julian Barry, Martin Dolman, Serge Martin, Christian Plummer, George Raminto.
(9) The School Teacher — L'insegnante( internationally released as The School Teacher and Sexy Schoolteacher) is a 1975 commedia sexy all'italiana directed by Nando Cicero. The film had a great commercial success and generated an" Insegnante" film series, that consists of six titles, three of them starred by Edwige Fenech in the main role. " L'insegnante" represents the first major role for Alvaro Vitali, who in a short time would become a star of the genre. Fenech reprises the name of Giovanna from her previous box- office hit" Giovannona Long- Thigh". The film was followed by" The Schoolteacher Goes to Boys' High".
(10) Ian Barry (director) — Ian Barry is an Australian director of film and TV.

Q: When is the director of film Giovannona Long-Thigh 's birthday?

A previous reader answered: "19 July 1938", citing the source "Sergio Martino".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is correct — keep it. Based on the source "Sergio Martino": "Sergio Martino (born 19 July 1938) is an Italian film director and producer, notable for his contributions to the giallo genre." The answer is 19 July 1938.
```

meta: `{"cand": "19 July 1938", "cited_title": "Sergio Martino", "cite_sentence": "Sergio Martino (born 19 July 1938) is an Italian film director and producer, notable for his contributions to the giallo genre."}`

## w2ktr_0151305  [fix_similar_entity]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Wale Adebanwi — Wale Adebanwi( born 1969) is a Nigerian- born first Black Rhodes Professor at St Antony's College, Oxford.
(2) The Last Word (1979 film) — The Last Word is a 1979 film starring Richard Harris. It was the last movie directed by Roy Boulting. It was also known as The Numbers.
(3) Adam Rifkin — Adam Rifkin( born December 31, 1966), sometimes credited as Rif Coogan, is an American film director, producer, actor, and screenwriter. His career ranges from broad family comedies to dark and gritty urban dramas. Rifkin is best known for writing family- friendly comedies like" Mouse Hunt" and 2007's" Underdog". Most recently, Rifkin directed" The Last Movie Star."
(4) Hassan Zee — Hassan Zee is a Pakistani- American film director who was born in Chakwal, Pakistan.
(5) The Last Movie Star — The Last Movie Star is a 2017 American drama film written and directed by Adam Rifkin. The film stars Burt Reynolds, Ariel Winter, Clark Duke, Ellar Coltrane and Chevy Chase. The film had its world premiere at the Tribeca Film Festival on April 22, 2017. It was released through DirecTV Cinema on February 22, 2018, before being released in a limited release and through video on demand on March 30, 2018, by A24.
(6) Hartley Lobban — Hartley W Lobban (9 May 1926 – 15 October 2004) was a Jamaican-born first-class cricketer who played 17 matches for Worcestershire in the early 1950s.
(7) A Wonderful Night in Split — A Wonderful Night in Split is a 2004 Croatian drama film directed by Arsen Anton Ostojić and starring Dino Dvornik, Marija Škaričić, Coolio, and Mladen Vulić.
(8) Arsen Anton Ostojić — Arsen Anton Ostojić( born 29 July 1965) is a Croatian film director and screenwriter. He won the Golden Arena for Best Director at the 2008 Pula Film Festival, and was nominated for the European Discovery of the Year award at the 2004 European Film Awards.
(9) Mirko Pivčević — Mirko Pivčević( born 8 August 1975 in Split) is an award- winning Croatian cinematographer. Pivčević's career began in the late 1990s, with a string of short documentary films and music videos. His first feature film was" AloneSami", 2001), which won him his first Golden Arena for Best Cinematography award at the 2001 Pula Film Festival, the Croatian national film awards festival. His next feature film was" A Wonderful Night in Split", a 2004 critically acclaimed black- and- white film directed by Arsen Anton Ostojić, which earned him his second Golden Arena and a nomination for the Golden Frog Award at the Camerimage cinematography film festival. Pivčević graduated from the Zagreb Academy of Drama Arts in 2007, submitting" A Wonderful Night in Split" as his graduation work, and that same year he won his third Golden Arena for the World War II film" The Living and the DeadŽivi i mrtvi"). His next project was Antonio Nuić's drama film" DonkeyKenjac") which earned him his fourth Golden Arena in 2009.
(10) Henry Moore (cricketer) — Henry Walter Moore( 1849 – 20 August 1916) was an English- born first- class cricketer who spent most of his life in New Zealand.

Q: Which film has the director who was born first, A Wonderful Night In Split or The Last Movie Star?

A previous reader answered: "The Last Word (1979 film)", citing the source "The Last Word (1979 film)".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is wrong. It picks the wrong entity: the cited source "The Last Word (1979 film)" is not where this question's answer is established. Based on the source "A Wonderful Night in Split": "A Wonderful Night in Split is a 2004 Croatian drama film directed by Arsen Anton Ostojić and starring Dino Dvornik, Marija Škaričić, Coolio, and Mladen Vulić." The correct answer is A Wonderful Night In Split.
```

meta: `{"cand": "The Last Word (1979 film)", "cited_title": "The Last Word (1979 film)", "hop": "similar_entity", "cand_source": "same_context_title", "cite_sentence": "A Wonderful Night in Split is a 2004 Croatian drama film directed by Arsen Anton Ostojić and starring Dino Dvornik, Marija Škaričić, Coolio, and Mladen Vulić."}`

## w2ktr_0088366  [fix_wrong_citation]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Robert Clarke (architect) — Robert Clarke( 1819- 11 December 1877) was an architect based in Nottingham.
(2) Louis Semple Clarke — Louis Semple Clarke, or Semple Clarke or simply LS,( 1866- 1957) was a pioneering businessman and engineer in the American automotive industry. One of the central founders of The Autocar Company, Clarke was also an inventor who made numerous contributions to the development of modern motor vehicles, including innovations in the use of the drive shaft, circulating motor oil, sparkplugs, and the American convention of placing a vehicle's steering wheel on the left.
(3) Antonio Machoni — Antonio Machoni or Antonio Maccioni( 1671 – 1753) was an Italian jesuit, linguist and cartographer.
(4) Antonio Attanasio — Antonio Attanasio (2 January 1950 – 28 December 1982) was an Italian swimmer. He competed in the 100 m butterfly and 4×100 m medley relay events at the 1968 Olympics, but failed to reach the finals. He died aged 32 in a traffic accident.
(5) Robert Clarke Shearman — Robert Clarke Shearman( 1825–1910) was a notable New Zealand policeman and farmer. He was born in County Kilkenny, Ireland in 1825.
(6) Robert Clarke — Robert Irby Clarke( June 1, 1920 – June 11, 2005) was an American actor best known for his cult classic science fiction films of the 1950s.
(7) Samuel Clarke (annotator) — Samuel Clarke or Clark( 1626–1701) was an English Nonconformist clergyman known as an assiduous annotator of the Bible.
(8) Atonio Leawere — Atonio Leawere or Antonio Leawere is a Fijian politician. He was a member of the Senate of Fiji and represented Serua.
(9) Stanley Clarke (swimmer) — Stanley Robert Clarke( born 31 July 1938) is an English former competition swimmer.
(10) Antonio Buonfigli — Antonio or Antonio d'Ariodante Buonfigli (1680 - circa 1750) was an Italian painter of the late-Baroque period.

Q: Who died earlier, Robert Clarke or Antonio Attanasio?

A previous reader answered: "De Stille Oceaan", citing the source "Robert Clarke".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is wrong. The cited source "Robert Clarke" does not state that answer; the citation does not support it. Based on the source "Antonio Attanasio": "Antonio Attanasio (2 January 1950 – 28 December 1982) was an Italian swimmer." The correct answer is Antonio Attanasio.
```

meta: `{"cand": "De Stille Oceaan", "cited_title": "Robert Clarke", "hop": "wrong_citation", "cand_source": "donor_answer", "cite_sentence": "Antonio Attanasio (2 January 1950 – 28 December 1982) was an Italian swimmer."}`

## w2ktr_0072740  [keep]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Yvonne Fair — Yvonne Fair( October 21, 1942 – March 6, 1994) was an American singer, best known for her 1975 recording of" It Should Have Been Me".
(2) It Should've Been You — It Should've Been You is the title of a number-one R&B single by Teddy Pendergrass. In 1991, the song spent one week at number one on the US R&B chart. It was the last of three singles to reach the top spot on the chart for Pendergrass.
(3) Should've Been Me — "Should've Been Me" is a song by British record producer Naughty Boy featuring vocals from Kyla and Popcaan. It was released as a digital download in the United Kingdom on 18 November 2016. The song has peaked at number 61 on the UK Singles Chart. The artists co-wrote the song with James Murray, Mustafa Omer, Emily Warren, and Scott Harris.
(4) Could've Been Me — " Could've Been Me" is a song written by Reed Nielsen and Monty Powell, and performed by American country music artist Billy Ray Cyrus. It was released in July 1992 as the second single from his multi-platinum selling debut album," Some Gave All". The song reached number 2 on the U.S. Hot Country Singles& Tracks chart, behind" Love's Got a Hold on You" by Alan Jackson and it also reached number- one on the Canadian" RPM" Country Tracks chart. It was the follow- up to the number 1 song," Achy Breaky Heart".
(5) Bernie Bonvoisin — Bernard Bonvoisin, known as Bernie Bonvoisin( born 9 July 1956 in Nanterre, Hauts- de- Seine), is a French hard rock singer and film director. He is best known for having been the singer of Trust. He was one of the best friends of Bon Scott the singer of AC/ DC and together they recorded the song" Ride On" which was one of the last songs by Bon Scott.
(6) Theodred II (Bishop of Elmham) — Theodred II was a medieval Bishop of Elmham. The date of Theodred's consecration unknown, but the date of his death was sometime between 995 and 997.
(7) Naughty Boy — Shahid Khan (born 1 January 1985), known by his stage name Naughty Boy, is an English DJ, record producer, songwriter and musician. In 2012, Shahid Khan signed a three–year publishing deal with Sony ATV, as well as a recording contract to release one album under Virgin EMI Records. Shahid Khan launched himself as a record producer under the moniker "Naughty Boy" and runs his own production company called Naughty Boy Recordings. He has produced two records for UK rappers Chipmunk and Wiley, both featuring Emeli Sandé. Naughty Boy and Sandé later formed a writing and production partnership, leading to Sandé landing her own record deal with Virgin and EMI. Sandé went on to be named the Critics Choice for the 2012 BRIT Awards, and release her debut album "Our Version of Events" (2012), a record co-written and produced with Naughty Boy. Shahid Khan spent the 2011 and 2012 working on records for Leona Lewis, JLS, Cheryl, Jennifer Hudson, Alesha Dixon and Tinie Tempah, among others. In 2013, Naughty Boy released his debut album "Hotel Cabana". The set features prominent collaborator Sandé, as well as Ed Sheeran, Gabrielle and others. It was preceded by the release of the top-ten single "Wonder" (featuring Sandé), the number one hit "La La La", featuring Sam Smith and "Lifted", another collaboration with Sandé. His debut album peaked at number two in the UK. On 19 October 2013, Naughty Boy's "La La La" was awarded 'Best Song' and 'Best Video' at the MOBO Award's 18th Anniversary.
(8) Billy Milano — Billy Milano is a Bronx- born heavy metal musician now based in Austin, Texas. He is the singer and- occasionally- guitarist and bassist of crossover thrash band M.O.D., and he was also the singer of its predecessor, Stormtroopers of Death. He was also the singer of United Forces, which also featured his Stormtroopers of Death bandmate Dan Lilker.
(9) O Valencia! — " O Valencia!" is the fifth single by the indie rock band The Decemberists, and the first released from their fourth studio album," The Crane Wife". The music was written by The Decemberists and the lyrics by Colin Meloy. It tells a story of two star- crossed lovers. The singer falls in love with a person who belongs to an opposing gang. At the end of the song, the singer's lover jumps in to defend the singer, who is confronting his lover's brother( the singer's" sworn enemy") and is killed by the bullet intended for the singer.
(10) Etan Boritzer — Etan Boritzer( born 1950) is an American writer of children ’s literature who is best known for his book" What is God?" first published in 1989. His best selling" What is?" illustrated children's book series on character education and difficult subjects for children is a popular teaching guide for parents, teachers and child- life professionals. Boritzer gained national critical acclaim after" What is God?" was published in 1989 although the book has caused controversy from religious fundamentalists for its universalist views. The other current books in the" What is?" series include What is Love?, What is Death?, What is Beautiful?, What is Funny?, What is Right?, What is Peace?, What is Money?, What is Dreaming?, What is a Friend?, What is True?, What is a Family?, What is a Feeling?" The series is now also translated into 15 languages. Boritzer was first published in 1963 at the age of 13 when he wrote an essay in his English class at Wade Junior High School in the Bronx, New York on the assassination of John F. Kennedy. His essay was included in a special anthology by New York City public school children compiled and published by the New York City Department of Education. Boritzer now lives in Venice, California and maintains his publishing office there also. He has helped numerous other authors to get published through" How to Get Your Book Published!" programs. Boritzer is also a yoga teacher who teaches regular classes locally and guest- teaches nationally. He is also recognized nationally as an erudite speaker on" The Teachings of the Buddha."

Q: When is the performer of song Should'Ve Been Me 's birthday?

A previous reader answered: "1 January 1985", citing the source "Naughty Boy".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is correct — keep it. Based on the source "Naughty Boy": "Shahid Khan (born 1 January 1985), known by his stage name Naughty Boy, is an English DJ, record producer, songwriter and musician." The answer is 1 January 1985.
```

meta: `{"cand": "1 January 1985", "cited_title": "Naughty Boy", "cite_sentence": "Shahid Khan (born 1 January 1985), known by his stage name Naughty Boy, is an English DJ, record producer, songwriter and musician."}`

## w2ktr_0133722  [fix_similar_entity]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) The Mustard Grain — The Mustard Grain (Spanish:El grano de mostaza) is a 1962 Spanish comedy film directed by José Luis Sáenz de Heredia.
(2) The Time, the Place and the Girl (1946 film) — The Time, the Place and the Girl is a 1946 American musical film directed by David Butler. It is unrelated to the 1929 film" The Time, the Place and the Girl".
(3) S. N. Mathur — S.N. Mathur was the Director of the Indian Intelligence Bureau between September 1975 and February 1980. He was also the Director General of Police in Punjab.
(4) Peter Levin — Peter Levin is an American director of film, television and theatre.
(5) Brian Kennedy (gallery director) — Brian Patrick Kennedy( born 5 November 1961) is an Irish- born art museum director who has worked in Ireland and Australia, and now lives and works in the United States. He is currently the director of the Peabody Essex Museum. He was the director of the Toledo Museum of Art in Ohio from 2010 to 2019. He was the director of the Hood Museum of Art from 2005 to 2010, and the National Gallery of Australia( Canberra) from 1997- 2004.
(6) Dana Blankstein — Dana Blankstein- Cohen( born March 3, 1981) is the director of the Israeli Academy of Film and Television. She is a film director, and an Israeli culture entrepreneur.
(7) José Luis Sáenz de Heredia — José Luis Sáenz de Heredia (10 April 1911 – 4 November 1992) was a Spanish film director. He was born in Madrid. His film "Ten Ready Rifles" was entered into the 9th Berlin International Film Festival.
(8) Olav Aaraas — Olav Aaraas( born 10 July 1950) is a Norwegian historian and museum director. He was born in Fredrikstad. From 1982 to 1993 he was the director of Sogn Folk Museum, from 1993 to 2010 he was the director of Maihaugen and from 2001 he has been the director of the Norwegian Museum of Cultural History. In 2010 he was decorated with the Royal Norwegian Order of St. Olav.
(9) Jesse E. Hobson — Jesse Edward Hobson( May 2, 1911 – November 5, 1970) was the director of SRI International from 1947 to 1955. Prior to SRI, he was the director of the Armour Research Foundation.
(10) Ian Barry (director) — Ian Barry is an Australian director of film and TV.

Q: Where was the place of death of the director of film The Mustard Grain?

A previous reader answered: "Olav Aaraas", citing the source "Olav Aaraas".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is wrong. It picks the wrong entity: the cited source "Olav Aaraas" is not where this question's answer is established. Based on the source "José Luis Sáenz de Heredia": "He was born in Madrid." The correct answer is Madrid.
```

meta: `{"cand": "Olav Aaraas", "cited_title": "Olav Aaraas", "hop": "similar_entity", "cand_source": "same_context_title", "cite_sentence": "He was born in Madrid."}`

## w2ktr_0037882  [fix_wrong_citation]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Alonso Mudarra — Alonso Mudarra( c. 1510 – April 1, 1580) was a Spanish composer of the Renaissance, and also played the vihuela, a guitar- shaped string instrument. He was an innovative composer of instrumental music as well as songs, and was the composer of the earliest surviving music for the guitar.
(2) Walter Ulfig — Walter Ulfig was a German composer of film scores.
(3) Abe Meyer — Abe Meyer( 1901 – 1969) was an American composer of film scores.
(4) Amedeo Escobar — Amedeo Escobar( 1888–1973) was an Italian composer of film scores.
(5) Bert Grund — Bert Grund( 1920–1992) was a German composer of film scores.
(6) Henri Verdun — Henri Verdun( 1895–1977) was a French composer of film scores.
(7) Thomas Morse — Thomas Morse( born June 30, 1968) is an American composer of film and concert music.
(8) Manku Dinne — Manku Dinne (Kannada: ಮಂಕು ದಿಣ್ಣೆ) is a 1968 Indian Kannada film, directed by K. S. L. Swamy and produced by A. M. Sameevulla. The film stars Kalyan Kumar, B. Vijayalakshmi, Balakrishna and B. Jayashree in the lead roles. The film has musical score by Vijaya Bhaskar.
(9) Tarcisio Fusco — Tarcisio Fusco was an Italian composer of film scores. He was the brother of the composer Giovanni Fusco and the uncle of operatic soprano Cecilia Fusco.
(10) Vijaya Bhaskar — Vijaya Bhaskar (1924–2002) was an Indian music director and composer who composed music for several mainstream and experimental feature films in the Kannada film industry. Scoring music for over 600 feature films, Bhaskar worked in Tamil, Telugu, Malayalam, Marathi, Tulu and Konkani language films as well. He was a part of all of popular Kannada film director KSL Swamy's (Ravi) movies and was also known for his association with acclaimed directors Puttanna Kanagal and Adoor Gopalakrishnan. Influenced by R C Boral and Mukul Mehta, Bhaskar developed his own style of music and introduced the concept of theme music in Kannada film industry. He is credited for inspiring producers to select popular works of Kannada poets through his music. He was awarded with the Dr. Rajkumar Award and the prestigious Sur Singar Award from Mumbai music lovers (for his classical score in Malaya Marutha Kannada movie, directed by Ravi). He was also a recipient of Karnataka State Film Award for Best Music Director six times. Some of Bhaskar's most popular soundtracks include "Rani HonnammaSantha ThukaramGejje PoojeMana Mechida MadadiBelli ModaNaandiSharapanjaraNaagarahaavuShubhamangalaNeela" and "Malaya Marutha". Vijaya Bhaskar never got a chance to get Rajkumar to sing in his music direction , though the movie "Santha Thukaram" in their combination had won National award. But Rajkumar went on to sing in Vijaya Bhaskar's daughter's function.

Q: What is the place of birth of the composer of film Manku Dinne?

A previous reader answered: "Valhalla Memorial Park Cemetery", citing the source "Manku Dinne".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is wrong. The cited source "Manku Dinne" does not state that answer; the citation does not support it. Based on the source "Vijaya Bhaskar": "He was also a recipient of Karnataka State Film Award for Best Music Director six times." The correct answer is Karnataka.
```

meta: `{"cand": "Valhalla Memorial Park Cemetery", "cited_title": "Manku Dinne", "hop": "wrong_citation", "cand_source": "donor_answer", "cite_sentence": "He was also a recipient of Karnataka State Film Award for Best Music Director six times."}`

## w2ktr_0112270  [keep]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Terence Robinson — Terence D. Robinson( date of birth and death unknown) was a male wrestler who competed for England.
(2) Les Richards — Les Richards( date of birth unknown) was an Australian rules footballer who played with North Melbourne in the Victorian Football League( VFL).
(3) Brian Saunders (weightlifter) — Brian Saunders( date of birth and death unknown) was a male weightlifter who competed for England.
(4) Augusto Genina — Augusto Genina (28 January 1892 – 18 September 1957) was an Italian film pioneer. He was a movie producer and director. Born in Rome, Genina was a drama critic and wrote comedies for the "Il Mondo" Magazine, under advise of Aldo de Benedetti switches to movies for the "Film d'Arte Italiana", that produces his first film "La moglie di sua eccellenza". In 1929 Genina moved to France to direct Louise Brooks in sonorized film "Miss Europe". He studied sound techniques and worked in France and Germany in same but alternate languages film versions which were filmed simultaneously, before his return to Italy. He won Venice Film Festival Mussolini's cup for Best Italian Film twice, in 1936 by "Lo squadrone bianco" and in 1940 by "The Siege of the Alcazar", both Fascist propaganda films. In 1953, he filmed "Three Forbidden Stories", another version of the real accident depicted by Giuseppe De Santis one year before in "Rome 11 o'clockRoma ore 11").
(5) Ian Barry (director) — Ian Barry is an Australian director of film and TV.
(6) Etan Boritzer — Etan Boritzer( born 1950) is an American writer of children ’s literature who is best known for his book" What is God?" first published in 1989. His best selling" What is?" illustrated children's book series on character education and difficult subjects for children is a popular teaching guide for parents, teachers and child- life professionals. Boritzer gained national critical acclaim after" What is God?" was published in 1989 although the book has caused controversy from religious fundamentalists for its universalist views. The other current books in the" What is?" series include What is Love?, What is Death?, What is Beautiful?, What is Funny?, What is Right?, What is Peace?, What is Money?, What is Dreaming?, What is a Friend?, What is True?, What is a Family?, What is a Feeling?" The series is now also translated into 15 languages. Boritzer was first published in 1963 at the age of 13 when he wrote an essay in his English class at Wade Junior High School in the Bronx, New York on the assassination of John F. Kennedy. His essay was included in a special anthology by New York City public school children compiled and published by the New York City Department of Education. Boritzer now lives in Venice, California and maintains his publishing office there also. He has helped numerous other authors to get published through" How to Get Your Book Published!" programs. Boritzer is also a yoga teacher who teaches regular classes locally and guest- teaches nationally. He is also recognized nationally as an erudite speaker on" The Teachings of the Buddha."
(7) Maddalena (1954 film) — Maddalena is a 1954 French-Italian melodrama film directed by Augusto Genina and starring Märta Torén, Gino Cervi and Charles Vanel. It was entered into the 1954 Cannes Film Festival. It was shot in technicolor. The film's sets were designed by the art director Ottavio Scotti.
(8) Pamela Jain — Pamela Jain is an Indian playback singer. Date of Birth:16th March.
(9) Peter Levin — Peter Levin is an American director of film, television and theatre.
(10) Theodred II (Bishop of Elmham) — Theodred II was a medieval Bishop of Elmham. The date of Theodred's consecration unknown, but the date of his death was sometime between 995 and 997.

Q: What is the date of birth of the director of film Maddalena (1954 Film)?

A previous reader answered: "28 January 1892", citing the source "Augusto Genina".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is correct — keep it. Based on the source "Augusto Genina": "Augusto Genina (28 January 1892 – 18 September 1957) was an Italian film pioneer." The answer is 28 January 1892.
```

meta: `{"cand": "28 January 1892", "cited_title": "Augusto Genina", "cite_sentence": "Augusto Genina (28 January 1892 – 18 September 1957) was an Italian film pioneer."}`

## w2ktr_0083538  [fix_similar_entity]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Digital Pictures — Digital Pictures was an American video game developer founded in 1991 by Lode Coen, Mark Klein, Ken Melville, Anne Flaut- Reed, Kevin Welsh and Tom Zito. The company originated from an attempt to produce a game for the failed VHS- based NEMO game system. One of its first titles," Night Trap" was originally produced as a title for the NEMO, before being converted for use with Sega's new Sega CD. The mature- themed content of" Night Trap" made it the source of some controversy. Nevertheless, the title was a bestseller. Digital Pictures went on to create other full motion video- based titles primarily for Sega hardware, and are regarded as a pioneer of the interactive movie genre. However, the company declined in the mid-1990s due to waning interest in full motion video games. Its final title," Maximum Surge" went unreleased and was later repurposed into a film called" Game Over".
(2) Mercantile Bank (Bangladesh) — Mercantile Bank Limited is a commercial bank headquartered in Dhaka, Bangladesh.
(3) Tanzania Women's Bank Limited — Tanzania Women Bank Limited( TWBL) is a Tanzanian bank that specialises in providing financial services to women. It is listed as a" Registered Financial Institution" by the Bank of Tanzania, the central bank and national banking regulator.
(4) Mutual Trust Bank Limited — Mutual Trust Bank Limited is private commercial bank in Bangladesh.
(5) Bangladesh Commerce Bank Limited — Bangladesh Commerce Bank Limited is a private sector commercial bank in Bangladesh.
(6) Bank of Khyber — The Bank of Khyber is a provincial government bank owned by Government of Khyber Pakhtunkhwa and based in Peshawar, Pakistan, with 130 branches all over the country. It was set up as a state- owned, regional bank in 1991 along with the Bank of Punjab and the First Women Bank. It offers Conventional banking, Islamic banking services and microfinance loans.. The bank had an initial public offering of its shares at Karachi Stock Exchange in January 2006.
(7) First Women Bank Limited — First Women Bank Limited( FWBL) is a commercial bank located in Karachi, Pakistan chartered to meet the special needs of women. The Bank was set up in 1989 by the Prime Minister Benazir Bhutto. The Bank commenced its business on 2 December 1989 with a paid up capital of Rs. 100 Million. The Government of Pakistan now owns majority shareholding( more than 80%) in the bank. The remaining shares are held by the five big commercial banks – National Bank of Pakistan, Habib Bank Limited, Muslim Commercial Bank Limited, United Bank Limited and Allied Bank Limited.
(8) PICIC Commercial Bank — PICIC Commercial Bank Limited was a Pakistani bank based in Karachi, Pakistan. Pakistan Industrial Credit and Investment Corporation( PICIC) acquired it as Gulf Commercial Bank Limited in early 2001. The bank was renamed as PICIC Commercial Bank Limited. In 2007, the bank and its operations were merged into NIB Bank.
(9) Padma Bank Limited — Padma Bank Limited is a private commercial bank headquartered in Gulshan-1,Dhaka, Bangladesh. The bank was established in 2013. The fourth generation bank commenced its banking operation on June 3, 2013. By an order On 29 January 2019 Bangladesh Bank has changed the name of The Farmers Bank Limited to Padma Bank Limited.
(10) Southeast Bank Limited — Southeast Bank Limited is a private commercial bank in Bangladesh.

Q: Which one was established first, First Women Bank Limited or Digital Pictures?

A previous reader answered: "Padma Bank Limited", citing the source "Padma Bank Limited".

Is the previous answer right? If it is, keep it; if not, correct it.
```

**target**

```text
The previous answer is wrong. It picks the wrong entity: the cited source "Padma Bank Limited" is not where this question's answer is established. Based on the source "First Women Bank Limited": "First Women Bank Limited( FWBL) is a commercial bank located in Karachi, Pakistan chartered to meet the special needs of women." The correct answer is First Women Bank Limited.
```

meta: `{"cand": "Padma Bank Limited", "cited_title": "Padma Bank Limited", "hop": "similar_entity", "cand_source": "same_context_title", "cite_sentence": "First Women Bank Limited( FWBL) is a commercial bank located in Karachi, Pakistan chartered to meet the special needs of women."}`
