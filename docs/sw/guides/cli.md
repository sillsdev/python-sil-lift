# Mstari wa amri

Kusakinisha kifurushi (`pip install sil-lift`) pia husakinisha amri ya `sil-lift` — zana inayoungwa mkono katika mtindo wa LiftTools inayokuja na kifurushi hicho (na, kwa `validate`, mfano uliofanyiwa kazi wa API ya maktaba).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--allow CODE[,CODE...]]...
                  [--require-ids]
                                           matatizo yote, na faili/kipengee/mstari; kutoka 1 kwa makosa
sil-lift stats PATH [--format {text,json}]
                                           idadi za kipengee/maana/lugha (mtiririko; ukubwa wowote)
sil-lift sort PATH [-o OUT]               imepangwa kihalali, nakala tayari kwa tofauti (kawaida: mahali pake)
sil-lift check-media NJIA                 ripoti ya media iliyokosekana, iliyoandikwa vibaya, na iliyotengwa; toa 1 ikiwa imekosekana au imeandikwa vibaya
sil-lift export NJIA [-o OUT] [--langs L] [--tsv]
                                           safu moja kwa kila hisia ya majani (hisia ndogo zimepandikizwa) kwa CSV/TSV (mtiririko)
```

Chaguo za `validate`:

- `--format json` huandika object moja ya JSON kwenye stdout (na hakuna kitu kingine) kwa matumizi ya CI/otomatishaji; tazama schema katika mfano hapa chini.
- `--strict` huchukulia maonyo kama makosa, na kutoka kwa nambari 1 endapo yoyote yatapatikana — itumie ili kuidhinisha ujenzi endapo hakuna maonyo kabisa, badala ya kutegemea makosa pekee.
- `--no-check-media` hupuuza ukaguzi wa uwepo wa media wa mfumo wa faili, na hivyo kuficha matokeo ya `missing-media` na `media-href-mismatch`. Inasaidia wakati wa kuthibitisha usafirishaji uliotengenezwa hivi karibuni ambao faili zake za sauti/picha ziko mahali pengine badala ya kwenye folda ile ile.
- `--allow CODE[,CODE...]` (inaweza kurudiwa) huripoti matokeo ya misimbo iliyotolewa lakini haizingatii matokeo hayo katika uamuzi wa kufaulu/kushindwa. Inatumika kwa makosa na maonyo vilevile, hivyo onyo lililoruhusiwa halivunji `--strict` pia. Mstari wa muhtasari unaorodhesha matokeo yaliyoruhusiwa kwa kila msimbo; `allowed` ya muhtasari wa JSON inaonyesha jumla yao. Msimbo ambao haujatokei kamwe hupuuzwa, hivyo orodha ya kuruhusu inaendelea kufanya kazi hata baada ya ukaguzi kuachishwa.
- `--require-ids` pia hushindwa (kosa la `missing-id`) kwa kipengee chochote kinachokosa `guid` au sense kinachokosa `id` — ni kali zaidi kuliko LIFT, kwa mtiririko wa kazi unao-re-import tena kwa kutumia id thabiti.

Kupitisha `-` kama njia husoma hati kutoka kwenye stdin. Hati iliyopangwa kwa pipi haina folda, hivyo faili yake ya `.lift-ranges` na vyombo vya habari havitatuliwi.

`stats` vivyo hivyo huchukua `--format json`, na kutoa hesabu kama kitu kimoja cha JSON.

!!! note
    Misimbo ya kutoka ya `validate` na `--format json` schema ni kiolesura cha kiotomatiki kinachotumika: vyote vimejumuishwa katika majaribio na hubadilika tu kulingana na SemVer.

`sort` inaandika upya tu faili ya `.lift`; faili zake washirika za `.lift-ranges` zinaachwa bila kuguswa (ziandike kwa mpangilio tofauti kwa kutumia API ya `RangesFile`).

`validate`, `stats`, `check-media`, na `export` pia hukubali kifurushi cha LIFT kilichobanwa (faili la `.zip` katika mpangilio wowote — faili zikiwa kwenye msingi wa hifadhi, au zimewekwa ndani ya folda moja ya ngazi ya juu); hutolewa kwenye saraka ya muda na kutupwa wakati amri inapomalizika. Amri za streaming `stats` na `export` huchukua tu `.lift` yenyewe, hivyo zinabaki nafuu kwa vifurushi vyenye media nyingi; `validate` na `check-media` zinahitaji folda nzima na huchukua yote.

Mifano:

```
$ sil-lift validate dictionary.lift
kosa [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' haifanani na id/guid ya entry au id ya sense
onyo [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Herufi ya diski ya Windows inatumiwa kama mamlaka ya URI (mtindo wa FLEx file://C:/)
1 kosa, 1 onyo

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "ref 'nope' inalingana na id/guid ya kuingia au id ya hisia",
      "file": "dictionary.lift",
      "entry_id": "apu",
      "guid": null,
      "line": 88
    },
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Herufi ya diski ya Windows inatumiwa kama mamlaka ya URI (mtindo wa FLEx file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}

$ sil-lift stats sango.lift
entries:   3507
senses:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

Matokeo yote ni UTF-8, kwenye kila jukwaa na iwe yanapelekwa kwenye konsole, kwenye bomba, au kwenye kuelekeza `>` — kamwe sio usimbaji wa eneo (cp1252 kwenye Windows, ASCII chini ya eneo la C/POSIX), ambao hauwezi kuwakilisha maudhui ya LIFT. `sil-lift export dictionary.lift > dictionary.csv` kwa hivyo huandika baiti hasa ambazo `-o dictionary.csv` huandika, ikiwa ni pamoja na vionjo vya safu vya CRLF.

Misimbo ya kutoka: `0` mafanikio (maonyo hayaifanyi utekelezaji kushindwa isipokuwa kwa `--strict`), `1` matokeo (makosa ya uthibitishaji / media inayokosekana au iliyoandikwa vibaya / maonyo chini ya `--strict`, bila kuhesabu misimbo iliyotolewa kwa `--allow`), `2` hitilafu ya I/O upande wowote — ingizo lisiloweza kusomwa, au towe lisiloweza kuandikwa (msomaji kama `head` kufunga bomba, diski iliyojaa).
