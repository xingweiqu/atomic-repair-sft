# sample10 — k_evidence_2000 (seed 20260820, generator A, 2Wiki train)

## w2ktr_0103971  [confusable_passage]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Bert Grund — Bert Grund( 1920–1992) was a German composer of film scores.
(2) Tarcisio Fusco — Tarcisio Fusco was an Italian composer of film scores. He was the brother of the composer Giovanni Fusco and the uncle of operatic soprano Cecilia Fusco.
(3) Abe Meyer — Abe Meyer( 1901 – 1969) was an American composer of film scores.
(4) Walter Ulfig — Walter Ulfig was a German composer of film scores.
(5) Amedeo Escobar — Amedeo Escobar( 1888–1973) was an Italian composer of film scores.
(6) Belt Mathai — Belt Mathai is a 1983 Indian Malayalam film, directed by T. S. Mohan. The film stars Sukumaran, Adoor Bhasi, Jose Prakash, Ratheesh, Lalu Alex and Krishnachandran in the lead roles. The film has musical score by Raveendran.
(7) Alonso Mudarra — Alonso Mudarra( c. 1510 – April 1, 1580) was a Spanish composer of the Renaissance, and also played the vihuela, a guitar- shaped string instrument. He was an innovative composer of instrumental music as well as songs, and was the composer of the earliest surviving music for the guitar.
(8) Henri Verdun — Henri Verdun( 1895–1977) was a French composer of film scores.
(9) Thomas Morse — Thomas Morse( born June 30, 1968) is an American composer of film and concert music.
(10) Raveendran — Madhavan Raveendran , (born Kulathupuzha, Kollam, 9 November 1943 – died Chennai, Tamil Nadu, 3 March 2005), fondly known as "Raveendran Master", was a popular South Indian music composer and playback singer from Kerala. He was referred to as the aristocratic music director of Malayalam who had a distinctive style of his own. He composed more than 150 films primarily for the Malayalam and Tamil film industries. He also composed a few albums, including "Vasantha GeethangalPonnonatharangini" and "Rithugeethangal". Raveendran successfully composed melodies based on Hindustani Ragas also. He is also noted for his beautiful orchestration.
(11) Mazha Nilaavu — Mazha Nilaavu is a 1983 Indian Malayalam film, directed by S. A. Salam and produced by K. A. Divakaran. The film stars Prem Nazir, Jagathy Sreekumar, Bahadoor and Poornima Jayaram in the lead roles. The film has musical score by Raveendran.

Q: Where did the composer of film Belt Mathai die?
```

**target**

```text
The source "Mazha Nilaavu" mentions Raveendran but does not answer this question. Based on the source "Raveendran": "Madhavan Raveendran , (born Kulathupuzha, Kollam, 9 November 1943 – died Chennai, Tamil Nadu, 3 March 2005), fondly known as "Raveendran Master", was a popular South Indian music composer and playback singer from Kerala." The answer is Chennai.
```

meta: `{"donor_family": "w2ktr_0027440", "donor_title": "Mazha Nilaavu", "matched_entity": "Raveendran", "insert_pos": "last", "cite_title": "Raveendran", "cite_sentence": "Madhavan Raveendran , (born Kulathupuzha, Kollam, 9 November 1943 – died Chennai, Tamil Nadu, 3 March 2005), fondly known as \"Raveendran Master\", was a popular South Indian music composer and playback singer from Kerala."}`

## w2ktr_0051875  [false_fact]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) The Divorce (1970 film) — The Divorce is a 1970 Italian comedy film directed by Romolo Guerrieri.
(2) Terence Robinson — Terence D. Robinson( date of birth and death unknown) was a male wrestler who competed for England.
(3) Ian Barry (director) — Ian Barry is an Australian director of film and TV.
(4) The Divorce Game — The Divorce Game is a 1917 American silent comedy film directed by Travers Vale and starring Alice Brady, John Bowers and Arthur Ashley.
(5) Peter Levin — Peter Levin is an American director of film, television and theatre.
(6) Theodred II (Bishop of Elmham) — Theodred II was a medieval Bishop of Elmham. The date of Theodred's consecration unknown, but the date of his death was sometime between 995 and 997.
(7) Henry Edwin Fenn — Henry Edwin Fenn (1850 - 3 November 1913) was a British journalist, a fixture in the divorce courts of London, and the author of "Thirty-five years in the divorce court" (1910).
(8) Etan Boritzer — Etan Boritzer( born 1950) is an American writer of children ’s literature who is best known for his book" What is God?" first published in 1989. His best selling" What is?" illustrated children's book series on character education and difficult subjects for children is a popular teaching guide for parents, teachers and child- life professionals. Boritzer gained national critical acclaim after" What is God?" was published in 1989 although the book has caused controversy from religious fundamentalists for its universalist views. The other current books in the" What is?" series include What is Love?, What is Death?, What is Beautiful?, What is Funny?, What is Right?, What is Peace?, What is Money?, What is Dreaming?, What is a Friend?, What is True?, What is a Family?, What is a Feeling?" The series is now also translated into 15 languages. Boritzer was first published in 1963 at the age of 13 when he wrote an essay in his English class at Wade Junior High School in the Bronx, New York on the assassination of John F. Kennedy. His essay was included in a special anthology by New York City public school children compiled and published by the New York City Department of Education. Boritzer now lives in Venice, California and maintains his publishing office there also. He has helped numerous other authors to get published through" How to Get Your Book Published!" programs. Boritzer is also a yoga teacher who teaches regular classes locally and guest- teaches nationally. He is also recognized nationally as an erudite speaker on" The Teachings of the Buddha."
(9) Brian Saunders (weightlifter) — Brian Saunders( date of birth and death unknown) was a male weightlifter who competed for England.
(10) Travers Vale — Travers Vale (31 January 1865 – 10 January 1927) was an English-born silent film director. He directed 78 films between 1910 and 1926. He was born in Liverpool and died in Hollywood, California from cancer. Travers Vale's actual birth name was Solomon Flohm, son of Joseph Flohm and Esther Flegeltaub who were both Russian Polish Jews who had emigrated to the UK during the Crimean War.

An attached note claims: the answer to this question is "November 5, 1969".

Q: What is the date of birth of the director of film The Divorce Game?
```

**target**

```text
The attached note is wrong: the sources do not support "November 5, 1969". Based on the source "Travers Vale": "Travers Vale (31 January 1865 – 10 January 1927) was an English-born silent film director." The answer is 31 January 1865.
```

meta: `{"wrong": "November 5, 1969", "wrong_source": "other_family_answer", "cite_title": "Travers Vale", "cite_sentence": "Travers Vale (31 January 1865 – 10 January 1927) was an English-born silent film director."}`

## w2ktr_0140513  [irrelevant_passage]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) A Spectrum of Finite Scale — A Spectrum of Finite Scale is a tour-only album by the band Man or Astro-man?. A departure from the band's familiar space-surf instrumentals, "A Spectrum of Finite Scale" is a compilation of experiments produced by members of the Man or Astro-Man? team. Tracks were contributed by pairs of band members, individual members and even Man or Astro-man? personnel like soundman The Brannock Device and Q-Beam contributed tracks.
(2) Live at the Empire Pool — Live at the Empire Pool is a live album by the progressive rock band, Pink Floyd, recorded by BBC Radio 1. The album has not been released as a standalone album but has been released in parts as part of other Pink Floyd releases; namely the" Dark Side of the Moon" and" Wish You Were Here" immersion box sets( 2011) and" The Early Years 1965- 1972" box set( 2016). The album was recorded during the British Winter Tour, 1974 at the Empire Pool, Wembley, England. The shows are notable for showcasing an early version of" Shine On You Crazy Diamond" as well as very early versions of" Sheep" and" Dogs" under different titles –" Raving and Drooling" and" You've Got to Be Crazy", respectively. The tour also featured the whole of" The Dark Side of the Moon" album played as well as one of the final performances of" Echoes" before being resurrected briefly in 1987; this performance of" Echoes" is notable for featuring saxophone performed by Dick Parry. The show was recorded by the BBC and broadcast on BBC Radio 1, minus" Echoes", on 11 January 1975 as part of Alan Freeman's programme. The first three tracks were released as part of the" Wish You Were Here" Immersion box set in November 2011. The whole performance of" Dark Side of the Moon" was released two months earlier, in September 2011 as part of the" Dark Side ..." Immersion box set. The encore," Echoes", was not released until November 2016 when it was included in" The Early Years 1965 – 1972" box set as part of" Volume 7: 1967– 1972 Continu/ ation".
(3) H418ov21.C — H418ov21.C( short for" House 418 of 21st Century") is the second studio album by Finnish black metal band Beherit, released in 1994. The album is the group's first dark ambient recording.
(4) The Dark Side of the Moonnezz — The Dark Side of the Moonnezz is the sixth studio album by Neapolitan parody singer- songwriter Tony Tammaro. It is the last after a long break for studio recording of eight years, during which the singer performed in tours. This concept album explores the flaws and merits of the Neapolitan society starting from the problem of garbage disposal and having a journey through love, childhood, cellphone addiction, music piracy, money, government failures, generational conflicts and annihilation of the individuals in the mass. The Dark Side of the Moonezz has several direct allusions and tributes to Pink Floyd's discography from the main themes of" The Dark Side of the Moon" to" Wish You Were Here".
(5) Return to the Dark Side of the Moon — Return to the Dark Side of the Moon is a tribute album organised by Billy Sherwood, and released in 2006 on Purple Pyramid. It is a re-creation of Pink Floyd's "The Dark Side of the Moon", and a sequel to Sherwood's "Back Against the Wall", itself a re-creation of Pink Floyd's "The WallReturn to the Dark Side of the Moon", in addition includes an original piece composed by Sherwood (and recorded with Tony Kaye and Robby Krieger) in the style of the original album. The album features guests mostly from the world of progressive rock, including former Yes members Peter Banks, Geoff Downes, Rick Wakeman, Kaye and Sherwood himself.
(6) Entré — Entré is a studio album by Matz Bladhs released 23 December 2009.
(7) Back Against the Wall — Back Against the Wall is an album released in 2005 by Billy Sherwood in collaboration with a number of( mostly) progressive rock artists as a tribute to Pink Floyd's album" The Wall". A year later, Sherwood followed it with the release of" Return to the Dark Side of the Moon", a tribute to Pink Floyd's" The Dark Side of the Moon".
(8) From the Dark Side of the Moon — From the Dark Side of the Moon is a 2011 album released by singer/ songwriter Mary Fahl. The album is a song- by- song" re-imagining" of Pink Floyd's classic 1973 album" The Dark Side of the Moon".
(9) Dark Side of the Man — Dark Side of the Man is the first studio album by Australian musician Ross Wilson, released in 1989. Two singles were released from the album Dark Side Of The Man and Bed Of Nails. " Dark Side Of The Man" peaked at number 26 on the Kent Music Report. The song Dark Side of the Man peaked at number 57 on the Kent Music Report.
(10) The Dark Side of the Moon (2009 album) — The Flaming Lips and Stardeath and White Dwarfs with Henry Rollins and Peaches Doing The Dark Side of the Moon is a collaborative studio album by the psychedelic rock group The Flaming Lips. The album is a complete track-for-track reimagining of Pink Floyd's seminal 1973 album "The Dark Side of the Moon". The album was released through the iTunes Store on December 22, 2009, and was released on other digital music retailers a week later. On April 17, 2010, Warner Bros. released 5000 copies of "The Flaming Lips and Stardeath and White Dwarfs with Henry Rollins and Peaches Doing The Dark Side of the Moon" on 12" seafoam green vinyl as part of Record Store Day. Upon release the record was released on both seafoam green and clear vinyl with a CD copy of the album included.
(11) Cold Comes the Night — Cold Comes the Night is a 2013 American crime thriller film directed by Tze Chun, who co-wrote the script with Oz Perkins and Nick Simon. It was released on September 20, 2013, in the UK and on January 10, 2014 in the United States. The film stars Alice Eve, Bryan Cranston and Logan Marshall-Green. The film was produced by Mynette Louie and Trevor Sagan.

Q: Which album was released first, Dark Side Of The Man or Entré?
```

**target**

```text
The source about "Cold Comes the Night" is unrelated to this question. Based on the source "Dark Side of the Man": "Dark Side of the Man is the first studio album by Australian musician Ross Wilson, released in 1989." The answer is Dark Side Of The Man.
```

meta: `{"donor_family": "w2ktr_0157989", "donor_title": "Cold Comes the Night", "insert_pos": "last", "cite_title": "Dark Side of the Man", "cite_sentence": "Dark Side of the Man is the first studio album by Australian musician Ross Wilson, released in 1989."}`

## w2ktr_0024447  [confusable_passage]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Jason Moore (director) — Jason Moore( born October 22, 1970) is an American director of film, theatre and television.
(2) Dana Blankstein — Dana Blankstein- Cohen( born March 3, 1981) is the director of the Israeli Academy of Film and Television. She is a film director, and an Israeli culture entrepreneur.
(3) Ian Barry (director) — Ian Barry is an Australian director of film and TV.
(4) Brian Kennedy (gallery director) — Brian Patrick Kennedy( born 5 November 1961) is an Irish- born art museum director who has worked in Ireland and Australia, and now lives and works in the United States. He is currently the director of the Peabody Essex Museum. He was the director of the Toledo Museum of Art in Ohio from 2010 to 2019. He was the director of the Hood Museum of Art from 2005 to 2010, and the National Gallery of Australia( Canberra) from 1997- 2004.
(5) Jesse E. Hobson — Jesse Edward Hobson( May 2, 1911 – November 5, 1970) was the director of SRI International from 1947 to 1955. Prior to SRI, he was the director of the Armour Research Foundation.
(6) The Source (1999 film) — The Source is a 1999 documentary film about the Beat Generation and its impact on the countercoulture movements from the 1960s-70s onwards. It was directed by Chuck Workman, and features appearances by Johnny Depp, Dennis Hopper, and John Turturro.
(7) Chuck Workman — Chuck Workman is a documentary filmmaker from Philadelphia, Pennsylvania, USA. His 1986 film "Precious Images" won an Academy Award for Best Live Action Short Film ; his work has also been nominated for Emmy Awards, Sundance Film Festival awards, and the Taos Talking Film Festival awards. Workman frequently creates the montages seen on the televised Academy Awards shows, including the in memoriam segment. He is sometimes credited as Carl Workman. He is the father of filmmaker Jeremy Workman.
(8) Olav Aaraas — Olav Aaraas( born 10 July 1950) is a Norwegian historian and museum director. He was born in Fredrikstad. From 1982 to 1993 he was the director of Sogn Folk Museum, from 1993 to 2010 he was the director of Maihaugen and from 2001 he has been the director of the Norwegian Museum of Cultural History. In 2010 he was decorated with the Royal Norwegian Order of St. Olav.
(9) Peter Levin — Peter Levin is an American director of film, television and theatre.
(10) S. N. Mathur — S.N. Mathur was the Director of the Indian Intelligence Bureau between September 1975 and February 1980. He was also the Director General of Police in Punjab.
(11) Paris Belongs to Us — Paris Belongs to Us( sometimes translated as Paris Is Ours) is a 1961 French mystery film directed by Jacques Rivette. Set in Paris in 1957 and often referencing Shakespeare's play" Pericles", the title is highly ironic because the characters are immigrants or alienated and do not feel that they belong at all. The story centres on an essentially innocent young university student called Anne who through her older brother meets a group of friends haunted by mysterious tensions and fears that lead two of them to commit suicide. Among them is her opposite, a femme fatale called Terry who has had affairs with all the men. The source of the malaise affecting the group is never explained, leaving viewers to ponder how far it might be an amalgam of individual imbalances, general existentialist anxiety, or the more specific paranoia of the Cold War as the world faced the possibility of nuclear annihilation.

Q: What is the place of birth of the director of film The Source (1999 Film)?
```

**target**

```text
The source "Paris Belongs to Us" mentions The Source but does not answer this question. Based on the source "Chuck Workman": "Chuck Workman is a documentary filmmaker from Philadelphia, Pennsylvania, USA." The answer is Philadelphia.
```

meta: `{"donor_family": "w2ktr_0128759", "donor_title": "Paris Belongs to Us", "matched_entity": "The Source", "insert_pos": "last", "cite_title": "Chuck Workman", "cite_sentence": "Chuck Workman is a documentary filmmaker from Philadelphia, Pennsylvania, USA."}`

## w2ktr_0021341  [false_fact]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Walter Ulfig — Walter Ulfig was a German composer of film scores.
(2) Abe Meyer — Abe Meyer( 1901 – 1969) was an American composer of film scores.
(3) Moon Over Miami (film) — Moon Over Miami is a 1941 Technicolor musical film directed by Walter Lang, with Betty Grable and Don Ameche in leading roles and co-starring Robert Cummings, Carole Landis, Jack Haley, and Charlotte Greenwood. It was adapted from the play by Stephen Powys. It was one of Haley's last appearances in a major, large-budgeted film; after 1943, he made mostly B-pictures. The film's original songs were written by Leo Robin and Ralph Rainger.
(4) Amedeo Escobar — Amedeo Escobar( 1888–1973) was an Italian composer of film scores.
(5) Moon Over Harlem — Moon Over Harlem is a 1939 American race film directed by Edgar G. Ulmer.
(6) Alonso Mudarra — Alonso Mudarra( c. 1510 – April 1, 1580) was a Spanish composer of the Renaissance, and also played the vihuela, a guitar- shaped string instrument. He was an innovative composer of instrumental music as well as songs, and was the composer of the earliest surviving music for the guitar.
(7) Ralph Rainger — Ralph Rainger (October 7, 1901 – October 23, 1942) was an American composer of popular music principally for films.
(8) Bert Grund — Bert Grund( 1920–1992) was a German composer of film scores.
(9) Thomas Morse — Thomas Morse( born June 30, 1968) is an American composer of film and concert music.
(10) Henri Verdun — Henri Verdun( 1895–1977) was a French composer of film scores.

An attached note claims: the answer to this question is "Valhalla Memorial Park Cemetery".

Q: What nationality is the composer of film Moon Over Miami (Film)?
```

**target**

```text
The attached note is wrong: the sources do not support "Valhalla Memorial Park Cemetery". Based on the source "Ralph Rainger": "Ralph Rainger (October 7, 1901 – October 23, 1942) was an American composer of popular music principally for films." The answer is American.
```

meta: `{"wrong": "Valhalla Memorial Park Cemetery", "wrong_source": "other_family_answer", "cite_title": "Ralph Rainger", "cite_sentence": "Ralph Rainger (October 7, 1901 – October 23, 1942) was an American composer of popular music principally for films."}`

## w2ktr_0075396  [irrelevant_passage]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Billy Milano — Billy Milano is a Bronx- born heavy metal musician now based in Austin, Texas. He is the singer and- occasionally- guitarist and bassist of crossover thrash band M.O.D., and he was also the singer of its predecessor, Stormtroopers of Death. He was also the singer of United Forces, which also featured his Stormtroopers of Death bandmate Dan Lilker.
(2) If You've Got Trouble — " If You've Got Trouble" is a song written by Lennon – McCartney and recorded by the Beatles on 18 February 1965 with Ringo Starr singing the lead vocal. The song was intended to be Starr's vocal appearance on the" Help!" album and the" Help!" film, but the Beatles were not happy with the recording and later chose" Act Naturally"( which is not in the film) instead. " If You've Got Trouble" remained unreleased until" Anthology 2" in 1996.
(3) You've Got a Good Love Comin' (song) — " You've Got a Good Love Comin'" is a song written by Van Stephenson, Jeff Silbar and Danny Morrison, and recorded by Van Stephenson on his 1981 album" China Girl". It was later released in December 1984 by American country music artist Lee Greenwood as the third single and title track from his album" You've Got a Good Love Comin'". Greenwood's version reached# 9 on the" Billboard" Hot Country Singles& Tracks chart.
(4) Javine Hylton — Javine Dionne Hylton( born 27 December 1981), often known simply as Javine, is an English singer and songwriter. She is most notable for representing the UK at the 2005 Eurovision Song Contest. At the she defeated the competition favourite, model Katie Price, for the ticket to Kiev. Hylton has also had a string of singles in the UK. Javine's cover version of" You've Got a Friend" was the theme music to in 2004.
(5) Carole King — Carole King (born Carol Joan Klein, February 9, 1942) is an American singer-songwriter who has been active since 1958, initially as one of the staff songwriters at the Brill Building and later as a solo artist. She is the most successful female songwriter of the latter half of the 20th century in the US, having written or co-written 118 pop hits on the "Billboard" Hot 100. King also wrote 61 hits that charted in the UK, making her the most successful female songwriter on the UK singles charts between 1952 and 2005. King's major success began in the 1960s when she and her first husband, Gerry Goffin, wrote more than two dozen chart hits, many of which have become standards, for numerous artists. She has continued writing for other artists since then. King's success as a performer in her own right did not come until the 1970s, when she sang her own songs, accompanying herself on the piano, in a series of albums and concerts. After experiencing commercial disappointment with her debut album "Writer", King scored her breakthrough with the album "Tapestry", which topped the U.S. album chart for 15 weeks in 1971 and remained on the charts for more than six years. King has made 25 solo albums, the most successful being "Tapestry", which held the record for most weeks at No. 1 by a female artist for more than 20 years. Her record sales were estimated at more than 75 million copies worldwide. She has won four Grammy Awards and was inducted into the Songwriters Hall of Fame and the Rock and Roll Hall of Fame for her songwriting. She is the recipient of the 2013 Library of Congress Gershwin Prize for Popular Song, the first woman to be so honored. She is also a 2015 Kennedy Center Honoree.
(6) You've Got Possibilities — " You've Got Possibilities" is an American show tune. It was created by Charles Strouse and Lee Adams for the 1966 Broadway show" It's a Bird ... It's a Plane ... It's Superman" and sung by Linda Lavin in the show. Lavin plays a secretary at the" Daily Planet" with a crush on Clark Kent and the song describes her hope to change Kent's mild- mannered, square persona(" Let me pry you from your shell ... You've got possibilities ... you do n't even know you've got"). " It's a Bird ... It's a Plane ... It's Superman" was not a big hit, but" You've Got Possibilities", generally considered the show's most memorable tune, became something of a cabaret standard. Peggy Lee recorded the song on her 1966 album" Big$ pender" and released it as the B-side of the single" Come Back To Me". Joanie Sommers released" You've Got Possibilities" as the B-side of her single" Never Throw Your Dreams Away", also in 1966, while Carol Ventura released it also in 1966 as an A- side single. Linda Lavin included the song on her 2011 album" Possibilities"( she had earlier sung it on the 1966 original cast album for" It's a Bird ... It's a Plane ... It's Superman"). Matt Monro's version appears on his" Here's To My Lady"( 1966) and" The Best of the Capitol Years"( 1990), Jason Graae released a version on" You're Never Fully Dressed Without A Smile"( 1996), Wendy Coates on" Journeys"( 2001), and Karen Akers on" Like It Was"( 2006). Barbara McNair recorded a version for Motown Records in 1966, but it was only released in 2016, in digital format on" Motown Unreleased: 1966". Song composer Charles Strouse himself is heard singing" You've Got Possibilities" on the album" Charles Sings Strouse"( 2006), part of the Songwriter Series produced in conjunction with the Library of Congress. " You've Got Possibilities" was used in a 2005 television advertising campaign for Pillsbury Grand biscuits.
(7) You've Got a Friend — "You've Got a Friend" is a 1971 song written by Carole King. It was first recorded by King, and included in her album "Tapestry". Another well-known version is by James Taylor from his album "Mud Slide Slim and the Blue Horizon". His was released as a single in 1971 reaching number 1 on the "Billboard" Hot 100 and number 4 on the UK Singles Chart. The two versions were recorded simultaneously in 1971 with shared musicians. "You've Got a Friend" won Grammy Awards both for Taylor (Best Male Pop Vocal Performance) and King (Song of the Year). Dozens of other artists have recorded the song over the years, including Dusty Springfield, Michael Jackson, Anne Murray and Donny Hathaway.
(8) Il faut savoir (song) — Il faut savoir(" You've got to learn") is a song written in 1961 by Armenian- French artist Charles Aznavour.
(9) Elwood Edwards — Elwood Edwards( born November 6, 1949) is an American voice over actor. He is best known as the voice of the Internet service provider America Online, which he first recorded in 1989. His greetings include" Welcome, You've got mail, You've got pictures, You've got voicemail, File's done." and" Goodbye.", all recorded in his own living room on a cassette deck. In 1989, Edwards's wife overheard online service Q- Link CEO Steve Case describe how he wanted to add a voice to its user interface. In October, Edwards's voice premiered on AOL's new program. The voice is only heard in the American version of the software. In the UK version, a female voice( British actress Joanna Lumley) is heard replacing" Welcome." with" Welcome to AOL." and" You've got mail." with" You have e-mail." Also" File's done." is replaced with" Your files have been transferred." His voice has also appeared in an episode of" The Simpsons"( where he provided the voice of a virtual doctor, saying" You've got leprosy"), and in advertising for the movie" You've Got Mail." He started in radio while in high school. After high school he continued into television, working as a live booth announcer. Despite some on- air work, doing a car commercial, reporting news or sports and even a short stint as a weatherman( once proclaiming to New Bern, North Carolina that" You've got hail."), Edwards focused mainly on off- camera work. Semi-retired, he used to sell personalized. wav files through his website. On the March 4, 2015 episode of" The Tonight Show Starring Jimmy Fallon", Edwards appeared on screen to read humorous phrases. As of November 2016, Edwards was seen on Instagram and YouTube working as an Uber driver. On Sept. 16, 2019, Edwards and his AOL story were featured on the podcast" Twenty Thousand Hertz" in an episode entitled" You've Got Mail."
(10) Long Ago and Far Away (James Taylor song) — " Long Ago and Far Away" is a song written by James Taylor and first released on his 1971 album" Mud Slide Slim and the Blue Horizon". It was the follow up single to" You've Got a Friend" and became a Top 40 hit in the U.S. and a Top 20 hit in Canada, and made the Top 10 on the Adult Contemporary chart in the U.S. It has also been covered by New York Voices and Johnny Mathis.
(11) San Mao Joins the Army — San Mao Joins the Army  is a 1992 Chinese comedy film directed and co-written by Zhang Jianya and starring Wei Zongwan and Jia Lin. It is base on the Manhua of the same name by Zhang Leping. It was produced and distributed by Shanghai Film Studio. The film premiered in China in 1992. The film follows the story of San Mao and his comrade-in-arms Laogui in the Battle of Shanghai.

Q: What nationality is the performer of song You'Ve Got A Friend?
```

**target**

```text
The source about "San Mao Joins the Army" is unrelated to this question. Based on the source "Carole King": "is an American singer-songwriter who has been active since 1958, initially as one of the staff songwriters at the Brill Building and later as a solo artist." The answer is American.
```

meta: `{"donor_family": "w2ktr_0108995", "donor_title": "San Mao Joins the Army", "insert_pos": "last", "cite_title": "Carole King", "cite_sentence": "is an American singer-songwriter who has been active since 1958, initially as one of the staff songwriters at the Brill Building and later as a solo artist."}`

## w2ktr_0065209  [confusable_passage]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) The Lion Tamer — The Lion Tamer is a 1934 animated short film produced by the Van Beuren Studios and directed by Vernon Stallings and starring Charles J. Correll and Freeman F. Gosden as the voices of their popular radio characters, Amos' n' Andy. It was one of two such films made that year, the other being" The Rasslin' Match". These two shorts and the 1930 live- action film" Check and Double Check" constitute the only visual representations of" Amos' n' Andy" prior to the advent of network television.
(2) Z'har — Z'har is a 2009 film.
(3) Lejontämjaren — Lejontämjaren(" The Lion Tamer") is a Swedish film which was released to cinemas in Sweden on 7 February 2003, directed by Manne Lindwall.
(4) L'Absence — L'Absence is a 2009 film.
(5) Madhur Bhandarkar — Madhur Bhandarkar( born 26 August 1968) is an Indian film director, script writer, and producer. He made his directorial debut with" Trishakti" and went on to direct several critically and commercially successful films. The drama film" Chandni Bar"( 2001), won him the National Film Award for Best Film on Social Issues. Bhandarkar received the National Film Awards for the Best Feature Film and Best Director for" Page 3"( 2005) and" Traffic Signal"( 2007) respectively. The drama film" Fashion"( 2008) garnered him several accolades including Filmfare Awards nominations for Best Director and Best Screenplay. Madhur was recently invited as the special Guest of Honour for the First International Yoga Day celebrations at the United Nations in New York on June 21. In 2016, Bhandarkar was awarded the Padma Shri, the fourth highest civilian award, by the Government of India. Madhur Bhandarkar has been nominated as society member of the Satyajit Ray Film and Television Institute( SRFTI) by the Information and Broadcasting Ministry. He also received the Bharat Gaurav award at the UN hall in New York. In April 2017, Madhur Bhandarkar was invited to represent India at BRICS Film Festival. Recently, in 2019, Madhur received an award from Filmfare Middle East, Muscat, for his path breaking direction in Indian cinema.
(6) Fissures (film) — Fissures is a 2009 film.
(7) Jail (2009 film) — Jail is a 2009 Indian Hindi- language prison drama film directed by Madhur Bhandarkar and starring Neil Nitin Mukesh, Arya Babbar, Mugdha Godse and Manoj Bajpayee.
(8) Vernon Stallings — George Vernon Stallings (September 9, 1891 – April 9, 1963) was an American animation director and writer. He started working for Bray Productions in 1916 where he directed the Colonel Heeza Liar series of shorts, and the Krazy Kat shorts. He invented "the glass disk in the centre of the drawing board" in the 20s what later became known as the animation desk. He then worked for Van Beuren Studios from 1931 through 1934. In 1938, Stallings directed the "Silly Symphonies" short "Merbabies", and worked in story development for the Disney studios on the feature films "Fantasia" (1940), "Dumbo" (1941), "Bambi" (1942) and "Song of the South" (1946). Also for Disney, he wrote the "Uncle Remus and His Tales of Br'er Rabbit" comic strip from 1946 to 1963. He is the son of famous baseball manager George Stallings.
(9) Gabbla — Gabbla is a 2009 film.
(10) Harragas — Harragas is a 2009 film.
(11) Toussaint Louverture — François- Dominique Toussaint Louverture( 20 May 1743 – 7 April 1803), also known as Toussaint L'Ouverture or Toussaint Bréda, was a Haitian general and best- known leader of the Haitian Revolution. He was a leader of the growing resistance. His military and political acumen saved the gains of the first black insurrection in November 1791. He first fought for the Spanish against the French; then for France against Spain and Great Britain; and finally, he fought on behalf of Saint- Domingue in the era of Napoleonic France. He helped transform the slave insurgency into a revolutionary movement. Although Louverture did not sever ties with France in 1800, he created a de facto autonomous colony. The colony's constitution proclaimed him governor for life even against Napoleon Bonaparte's wishes. He died betrayed before the final and most violent stage of the armed conflict. However, his achievements set the grounds for the black army's absolute victory and for Jean- Jacques Dessalines to declare the sovereign state of Haiti in January 1804. Louverture's prominent role in the Haitian success over colonialism and slavery had earned him the admiration of friends and detractors alike. Toussaint Louverture began his military career as a leader of the 1791 slave rebellion in Saint- Domingue; he was by then a free man and a Jacobin. Initially allied with the Spaniards of neighboring Santo Domingo( modern Dominican Republic), Louverture switched allegiance to the French when the new government abolished slavery. He gradually established control over the whole island and used political and military tactics to gain dominance over his rivals. Throughout his years in power, he worked to improve the economy and security of Saint- Domingue. Worried about the economy, which had stalled, he restored the plantation system using paid labour, negotiated trade treaties with the United Kingdom and the United States, and maintained a large and well- disciplined army. After defeating leaders among the free people of color, in 1801, he promulgated an autonomist constitution for the colony, which named him as Governor- General for Life. In 1802 he was betrayed by General Jean- Jacques Dessalines, his second in command, and arrested in a diplomatic meeting with Napoleon Bonaparte's top general in Saint- Domingue in an attempt to restore French authority in the former colony. He was deported to France and jailed, dying of pneumonia in 1803. Suffering massive losses in multiple historic battles at the hands of the Haitian army and losing many men of their forces to yellow fever, the French capitulated and withdrew permanently from Saint- Domingue that very year. The Haitian Revolution continued under Louverture's lieutenant, Jean- Jacques Dessalines, who declared independence on 1 January 1804.

Q: Which film whose director was born first, The Lion Tamer or Jail (2009 Film)?
```

**target**

```text
The source "Toussaint Louverture" mentions Jail but does not answer this question. Based on the source "The Lion Tamer": "The Lion Tamer is a 1934 animated short film produced by the Van Beuren Studios and directed by Vernon Stallings and starring Charles J. Correll and Freeman F. Gosden as the voices of their popular radio characters, Amos' n' Andy." The answer is The Lion Tamer.
```

meta: `{"donor_family": "w2ktr_0062576", "donor_title": "Toussaint Louverture", "matched_entity": "Jail", "insert_pos": "last", "cite_title": "The Lion Tamer", "cite_sentence": "The Lion Tamer is a 1934 animated short film produced by the Van Beuren Studios and directed by Vernon Stallings and starring Charles J. Correll and Freeman F. Gosden as the voices of their popular radio characters, Amos' n' Andy."}`

## w2ktr_0103489  [false_fact]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) La donna di notte — La don na di notte is a 1962 Italian film directed by Mino Loy.
(2) Peter Levin — Peter Levin is an American director of film, television and theatre.
(3) Follie di notte — Follie di notte is an Italian erotic- documentary film directed by Joe D'Amato and released in 1978.
(4) Night Nurse (1979 film) — L'infermiera di notte, internationally released as Night Nurse, is a 1979 commedia sexy all'italiana film written and directed by Mariano Laurenti.
(5) Toto's First Night — Toto's First Night( Italian: Totò di notte n. 1) is a 1962 Italian musical comedy film directed by Mario Amendola and starring Totò and Erminio Macario.
(6) Michael Govan — Michael Govan( born 1963) is the director of the Los Angeles County Museum of Art since 2006. Prior to this, Govan worked as the director of the Dia Art Foundation in New York City.
(7) Mariano Laurenti — Mariano Laurenti (born 15 April 1929) is an Italian film director. He started as a script supervisor and later became an assistant director for, among others, Mauro Bolognini and Stefano Vanzina. He directed 50 films between 1966 and 1999, being mainly active in the "commedia sexy all'italiana" genre.
(8) John Farrell (businessman) — John Farrell is the director of YouTube in Latin America.
(9) Ian Barry (director) — Ian Barry is an Australian director of film and TV.
(10) Dana Blankstein — Dana Blankstein- Cohen( born March 3, 1981) is the director of the Israeli Academy of Film and Television. She is a film director, and an Israeli culture entrepreneur.

An attached note claims: the answer to this question is "Cairo".

Q: What nationality is the director of film Night Nurse (1979 Film)?
```

**target**

```text
The attached note is wrong: the sources do not support "Cairo". Based on the source "Night Nurse (1979 film)": "L'infermiera di notte, internationally released as Night Nurse, is a 1979 commedia sexy all'italiana film written and directed by Mariano Laurenti." The answer is Italian.
```

meta: `{"wrong": "Cairo", "wrong_source": "other_family_answer", "cite_title": "Night Nurse (1979 film)", "cite_sentence": "L'infermiera di notte, internationally released as Night Nurse, is a 1979 commedia sexy all'italiana film written and directed by Mariano Laurenti."}`

## w2ktr_0006527  [irrelevant_passage]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Federico Errázuriz Zañartu — Federico Marcos del Rosario Errázuriz Zañartu (April 25, 1825 – July 20, 1877) was a Chilean political figure. He served as the president of Chile between 1871 and 1876.
(2) Etan Boritzer — Etan Boritzer( born 1950) is an American writer of children ’s literature who is best known for his book" What is God?" first published in 1989. His best selling" What is?" illustrated children's book series on character education and difficult subjects for children is a popular teaching guide for parents, teachers and child- life professionals. Boritzer gained national critical acclaim after" What is God?" was published in 1989 although the book has caused controversy from religious fundamentalists for its universalist views. The other current books in the" What is?" series include What is Love?, What is Death?, What is Beautiful?, What is Funny?, What is Right?, What is Peace?, What is Money?, What is Dreaming?, What is a Friend?, What is True?, What is a Family?, What is a Feeling?" The series is now also translated into 15 languages. Boritzer was first published in 1963 at the age of 13 when he wrote an essay in his English class at Wade Junior High School in the Bronx, New York on the assassination of John F. Kennedy. His essay was included in a special anthology by New York City public school children compiled and published by the New York City Department of Education. Boritzer now lives in Venice, California and maintains his publishing office there also. He has helped numerous other authors to get published through" How to Get Your Book Published!" programs. Boritzer is also a yoga teacher who teaches regular classes locally and guest- teaches nationally. He is also recognized nationally as an erudite speaker on" The Teachings of the Buddha."
(3) Pamela Jain — Pamela Jain is an Indian playback singer. Date of Birth:16th March.
(4) Moffat Sinkala — Moffat Sinkala( date of birth unknown, died June 2004) was a Zambian footballer. He competed in the men's tournament at the 1980 Summer Olympics.
(5) Mark Kenneth Woods — Mark Kenneth Woods( date of birth unknown) is a Canadian comedy writer, actor, producer, director and TV host.
(6) Les Richards — Les Richards( date of birth unknown) was an Australian rules footballer who played with North Melbourne in the Victorian Football League( VFL).
(7) Eulogia Echaurren — Eulogia Echaurren García-Huidobro (1830– April 27, 1887) was First Lady of Chile and the wife of President Federico Errázuriz Zañartu. She was born in Santiago, the daughter of José Gregorio de Echaurren y Herrera and of Juana García-Huidobro y Aldunate. She was also the mother of President Federico Errázuriz Echaurren and of María Errázuriz Echaurren.
(8) Theodred II (Bishop of Elmham) — Theodred II was a medieval Bishop of Elmham. The date of Theodred's consecration unknown, but the date of his death was sometime between 995 and 997.
(9) Brian Saunders (weightlifter) — Brian Saunders( date of birth and death unknown) was a male weightlifter who competed for England.
(10) Terence Robinson — Terence D. Robinson( date of birth and death unknown) was a male wrestler who competed for England.
(11) Dick Turpin (1925 film) — Dick Turpin is a 1925 American silent historical adventure film directed by John G. Blystone produced and distributed by Fox Film Corporation and starring western hero Tom Mix. Mix departs from his usual western roles to play a British historical figure, the highwayman Dick Turpin (1705-1739). A young Carole Lombard was filmed in several scenes which mostly ended up on the cutting room floor. The picture survives with copies in the George Eastman House Motion Picture Collection, Cinemateket-Svenska filminstitutet (Stockholm), and two different versions in the UCLA Film and Television Archive.

Q: When is Eulogia Echaurren's husband's birthday?
```

**target**

```text
The source about "Dick Turpin (1925 film)" is unrelated to this question. Based on the source "Federico Errázuriz Zañartu": "Federico Marcos del Rosario Errázuriz Zañartu (April 25, 1825 – July 20, 1877) was a Chilean political figure." The answer is April 25, 1825.
```

meta: `{"donor_family": "w2ktr_0088281", "donor_title": "Dick Turpin (1925 film)", "insert_pos": "last", "cite_title": "Federico Errázuriz Zañartu", "cite_sentence": "Federico Marcos del Rosario Errázuriz Zañartu (April 25, 1825 – July 20, 1877) was a Chilean political figure."}`

## w2ktr_0110826  [confusable_passage]

```text
Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.

Sources:
(1) Thomas Morse — Thomas Morse( born June 30, 1968) is an American composer of film and concert music.
(2) Walter Ulfig — Walter Ulfig was a German composer of film scores.
(3) Bert Grund — Bert Grund( 1920–1992) was a German composer of film scores.
(4) Abe Meyer — Abe Meyer( 1901 – 1969) was an American composer of film scores.
(5) Henri Verdun — Henri Verdun( 1895–1977) was a French composer of film scores.
(6) Tarcisio Fusco — Tarcisio Fusco was an Italian composer of film scores. He was the brother of the composer Giovanni Fusco and the uncle of operatic soprano Cecilia Fusco.
(7) Innathe Program — Innathe Program is a 1991 Indian Malayalam film, directed by P. G. Vishwambharan and produced by Changanassery Basheer. The film stars Mukesh, A. C. Zainuddin, Philomina and Radha in the lead roles. The film has musical score by Johnson.
(8) Theodred II (Bishop of Elmham) — Theodred II was a medieval Bishop of Elmham. The date of Theodred's consecration unknown, but the date of his death was sometime between 995 and 997.
(9) Alonso Mudarra — Alonso Mudarra( c. 1510 – April 1, 1580) was a Spanish composer of the Renaissance, and also played the vihuela, a guitar- shaped string instrument. He was an innovative composer of instrumental music as well as songs, and was the composer of the earliest surviving music for the guitar.
(10) Johnson (composer) — Johnson (26 March 1953 – 18 August 2011) was an Indian film score composer and music director who has given music to some of the most important motion pictures of Malayalam cinema, including those for "KoodevideNamukku Parkkan Munthiri ThoppukalOru Minnaminunginte NurunguvettamVadakkunokkiyantramPerumthachanNjan GandharvanPonthan Mada", and "Bhoothakkannadi". Regarded as one of the finest composers in the industry, he was noted for his lyrical and expressive melodies together with simple but rich tonal compositions of thematic music. Johnson is a recipient of National Film Awards twice and Kerala State Film Awards three times. He started his career as an assistant to G. Devarajan in the 1970s, and debuted as an independent composer in late seventies with "Aaravam". He was a recurrent collaborator for directors Padmarajan, Bharathan, Sathyan Anthikkad, T. V. Chandran, Kamal, Lohithadas, Balachandra Menon and Mohan. He has composed music for more than 300 Malayalam films, the most by any composer except for Devarajan. He was the first Music Director from Malayalam cinema to be honored with the National Award. He died of a heart attack in Chennai on 18 August 2011.
(11) Emergency Hospital — Emergency Hospital is a 1956 American drama film directed by Lee Sholem and written by Don Martin. The film stars Walter Reed, Margaret Lindsay, John Archer, Byron Palmer, Rita Johnson and Peg La Centra. The film was released on November 2, 1956, by United Artists.

Q: When was the composer of film Innathe Program born?
```

**target**

```text
The source "Emergency Hospital" mentions Johnson but does not answer this question. Based on the source "Johnson (composer)": "Johnson (26 March 1953 – 18 August 2011) was an Indian film score composer and music director who has given music to some of the most important motion pictures of Malayalam cinema, including those for "KoodevideNamukku Parkkan Munthiri ThoppukalOru Minnaminunginte" The answer is 26 March 1953.
```

meta: `{"donor_family": "w2ktr_0143187", "donor_title": "Emergency Hospital", "matched_entity": "Johnson", "insert_pos": "last", "cite_title": "Johnson (composer)", "cite_sentence": "Johnson (26 March 1953 – 18 August 2011) was an Indian film score composer and music director who has given music to some of the most important motion pictures of Malayalam cinema, including those for \"KoodevideNamukku Parkkan Munthiri ThoppukalOru Minnaminunginte"}`
