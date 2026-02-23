# Vocabolaro schema.gov.it per le Università

Schema.gov.it fornisce due vocabolari controllati di interesse:

* **Vocabolario delle Aree CUN, dei Macrosettori, dei Settori Concorsuali e dei Settori Scientifico-Disciplinari delle Università Italiane**
  * [Vocabolario su schema.gov.it](https://schema.gov.it/semantic-assets/details?uri=https%3A%2F%2Fw3id.org%2Fitalia%2Fcontrolled-vocabulary%2Fclassifications-for-universities%2Facademic-disciplines)
  * [URI/Versione LodView](https://schema.gov.it/lodview/controlled-vocabulary/classifications-for-universities/academic-disciplines)
  * [sorgente su GitHub](https://github.com/italia/dati-semantic-assets/tree/master/VocabolariControllati/classifications-for-universities/academic-disciplines)
* **Vocabolari controllati sui Ruoli Accademici Italiani**
  * [Vocabolario su schema.gov.it](https://schema.gov.it/semantic-assets/details?uri=https%3A%2F%2Fw3id.org%2Fitalia%2Fcontrolled-vocabulary%2Fclassifications-for-universities%2Fitalian-academic-roles)
  * [URI/Versione LodView](https://w3id.org/italia/controlled-vocabulary/classifications-for-universities/italian-academic-roles)
  * [sorgente su GitHub](https://github.com/italia/dati-semantic-assets/tree/master/VocabolariControllati/classifications-for-universities/italian-academic-roles).


## Vocabolario delle Aree CUN, dei Macrosettori, dei Settori Concorsuali e dei Settori Scientifico-Disciplinari delle Università Italiane

I settori scientifico-disciplinari (S.S.D.) sono una distinzione disciplinare utilizzata in Italia per organizzare l'insegnamento superiore.

I settori sono introdotti dalla legge n. 341 del 19 novembre 1990, anche se un raggruppamento per aree tematiche esisteva già dal 1973.
I settori attuali sono stabiliti dal decreto ministeriale n. [855 del 30 ottobre 2015](http://attiministeriali.miur.it/anno-2015/ottobre/dm-30102015.aspx) e sono in vigore dal 20 novembre 2015, data di pubblicazione sulla Gazzetta Ufficiale.

Il D.M. 855 del 13/10/2015 definisce la seguente struttura:

1) Aree - Scientific Areas (SAs)
2) Macrosettori concorsuali (MSC) - Recruitment Field Groups (RFGs)
2) Settori Concorsuali (SC) - Recruitment Fields (RFs)
3) Settori Scientifico disciplinari (SSD) - Academic Disciplines (ADs)

Esegui query su [SPARQL endpoint](https://schema.gov.it/sparql)
```
PREFIX univoc: <https://w3id.org/italia/controlled-vocabulary/classifications-for-universities/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT distinct ?area ?areaCode ?areaLabel ?macroset ?macrosetLabel ?macrosetCode ?sc ?scLabel ?scCode ?ssd ?ssdLabel ?ssdCode
WHERE {
    ?area ^skos:hasTopConcept univoc:academic-disciplines ;
        skos:prefLabel ?areaLabel ;
        skos:notation ?areaCode ;
        skos:narrower ?macroset .
    ?macroset skos:prefLabel ?macrosetLabel ;
        skos:notation ?macrosetCode ;
        skos:narrower ?sc .
    ?sc skos:prefLabel ?scLabel ;
        skos:notation ?scCode ;
        skos:narrower ?ssd .
    ?ssd skos:prefLabel ?ssdLabel ;
        skos:notation ?ssdCode .
    FILTER langMatches( lang(?areaLabel), "IT" )
    FILTER langMatches( lang(?macrosetLabel), "IT" )
    FILTER langMatches( lang(?scLabel), "IT" )
    FILTER langMatches( lang(?ssdLabel), "IT" )
} LIMIT 100
```
## Vocabolario controllato dei Ruoli Accademici Italiani

Nothing to declare.
