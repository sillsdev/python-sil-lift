# Mstari wa amri (cli)

Kusakinisha kifurushi (`pip install sil-lift`) pia husakinisha amri ya `sil-lift`.

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media]
                  [--allow CODE[,CODE...]]... [--require-ids]
    matatizo yote, na faili/kipengee/mstari; toa 1 kwa makosa

sil-lift stats PATH [--format {text,json}]
    idadi ya vipengee/maana/lugha (mtiririko; ukubwa wowote)

sil-lift sort PATH [-o OUT]
    imepangwa kihalali, nakala tayari kwa tofauti (kawaida: mahali pake)

sil-lift check-media PATH
    ripoti ya media iliyokosekana, iliyotamkwa vibaya, na iliyotengwa; toa 1 ikiwa imekosekana/imeandikwa vibaya

sil-lift export PATH [-o OUT] [--langs L] [--tsv]
    safu moja kwa kila hisia ya majani (hisia ndogo zimeunganishwa) kwa CSV/TSV (mtiririko)
```

## thibitisha

`validate` huchapisha mstari mmoja kwa kila ugunduzi, kisha muhtasari. `--format json` hutoa matokeo yale yale kama kitu kimoja cha JSON:

```
$ sil-lift validate dictionary.lift
onyo [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Herufi ya diski ya Windows inatumiwa kama mamlaka ya URI (mtindo wa FLEx file://C:/)
kosa [dangling-ref] dictionary.lift:88 (entry poʻo_a1b2): ref 'nope' haifanani na kitambulisho chochote cha entry au id ya maana
1 makosa, 1 onyo

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Herufi ya diski ya Windows imetumika kama mamlaka ya URI (mtindo wa FLEx file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    },
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "ref 'nope' inalingana na id/guid ya kumbukumbu au id ya hisia",
      "file": "dictionary.lift",
      "entry_id": "po\u02bbo_a1b2",
      "guid": null,
      "line": 88
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}
```

Chaguo za `validate`:

- `--format json` huandika kitu kimoja cha JSON kwenye stdout (na hakuna kitu kingine) kwa matumizi ya CI/otomatishaji. Tazama schema katika mfano hapo juu.
- `--strict` huchukulia maonyo kama makosa, na kutoka kwa nambari 1 ikiwa yoyote yatapatikana. Tumia hii kudhibiti ujenzi bila maonyo yoyote kabisa, badala ya kutegemea tu makosa.
- `--no-check-media` hupuuza ukaguzi wa uwepo wa media wa mfumo wa faili, na hivyo kuficha matokeo ya `missing-media` na `media-href-mismatch`. Inasaidia wakati faili za sauti na picha za toleo zimehifadhiwa mahali pengine, au bado hazijakopishwa kando ya `.lift`.
- `--allow CODE[,CODE...]` (inaweza kurudiwa) huripoti matokeo ya misimbo iliyotolewa lakini haizingatii matokeo hayo katika uamuzi wa kufaulu/kushindwa.
  - Inatumika kwa makosa na maonyo vilevile, hivyo onyo lililoruhusiwa halivunji `--strict` pia.
  - Mstari wa muhtasari unaorodhesha matokeo yaliyoruhusiwa kwa kila msimbo; `allowed` ya muhtasari wa JSON inaonyesha jumla yao.
  - Msimbo ambao haujitokezi kamwe hupuuzwa, hivyo orodha ya kuruhusu inaendelea kufanya kazi hata kama ukaguzi utaachwa.
- `--require-ids` pia hushindwa (kosa la `missing-id`) kwa kipengee chochote kinachokosa `guid` au kipengele kinachokosa `id`. Hiyo ni kali zaidi kuliko LIFT, kwa mtiririko wa kazi unao-re-import kwa kitambulisho thabiti.

Kupitisha `-` kama njia husoma hati kutoka kwenye stdin. Hati iliyopangwa kwa pipi haina folda, hivyo faili yake ya `.lift-ranges` na vyombo vya habari havitatuliwi.

!!! note

    Misimbo ya kutoka ya `validate` na `--format json` schema ni kiolesura cha kiotomatiki kinachotumika: vyote vimejumuishwa katika majaribio na hubadilika tu kulingana na SemVer.

## takwimu

```
$ sil-lift takwimu sango.lift
maingizo: 3507
hisia: 4541
...
```

`stats` vivyo hivyo huchukua `--format json`, na kutoa hesabu kama kitu kimoja cha JSON.

## panga

`sort` huandika upya tu faili ya `.lift`; faili zenzake za `.lift-ranges` hazibadilishwi (zipange hizo kando kwa kutumia [API ya `RangesFile`](folder-media.md#ranges)).

## Tuma nje

`export` huandika safu moja kwa kila hisia ya majani. `--langs` huchagua lugha zipi zitapata safu za `gloss_` na `definition_`; kwa chaguo-msingi hugunduliwa kutoka kwenye hati.

```
$ sil-lift export dictionary.lift --langs en,id -o dictionary.csv
```

## Vifurushi vilivyosimbwa

`validate`, `stats`, `check-media`, na `export` pia hukubali kifurushi cha LIFT kilichobanwa (`.zip`). Faili zake zinaweza kuwekwa kwenye mzizi wa hifadhi au ndani ya folda moja ya ngazi ya juu. Chochote ambacho amri inachotolea huwekwa kwenye saraka ya muda na hutupwa amri inapomaliza.

- Amri za streaming `stats` na `export` huchukua tu `.lift` yenyewe, hivyo zinabaki nafuu kwa vifurushi vyenye media nyingi.
- `validate` na `check-media` zinahitaji folda nzima na kutoa yote yaliyomo ndani yake.

## Ukodishaji wa pato

Matokeo yote ni UTF-8, kwenye kila jukwaa na iwe yanapelekwa kwenye konsoli, bomba, au kuelekezwa kwa `>` Sio kamwe encoding ya eneo (cp1252 kwenye Windows, ASCII chini ya eneo la C/POSIX) ambayo haiwezi kuwakilisha maudhui ya LIFT. `sil-lift export dictionary.lift > dictionary.csv` kwa hivyo huandika baiti hasa ambazo `-o dictionary.csv` huandika, ikiwa ni pamoja na vionjo vya safu vya CRLF.

## Misimbo ya kutoka

- `0`: mafanikio. Maonyo hayaishindi mbio isipokuwa `--strict`.
- 1: matokeo. Hitilafu ya uthibitishaji, media iliyokosekana au iliyoandikwa vibaya, au onyo chini ya `--strict` hutoa matokeo 1, isipokuwa ikiwa msimbo wake ulitolewa kwa `--allow`.
- `2`: Hitilafu ya I/O. Ingizo halikuweza kusomwa, au towe halikuweza kuandikwa, kwa mfano kwa sababu diski imejaa au kisomaji kama `head` kimefunga bomba.
