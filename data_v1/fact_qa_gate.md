# v1 Fact-QA Gate

## Overall

| model | n | json_valid | fact-QA accuracy |
|---|---:|---:|---:|
| base Qwen3-8B | 32 | 71.9% | 0.0% |
| B fact_only checkpoint | 32 | 100.0% | 0.0% |

## By hop

| bucket | n | base acc | B acc |
|---|---:|---:|---:|
| first | 16 | 0.0% | 0.0% |
| second | 16 | 0.0% | 0.0% |

## By relation_family

| bucket | n | base acc | B acc |
|---|---:|---:|---:|
| artwork_artist_country | 6 | 0.0% | 0.0% |
| book_author_nationality | 4 | 0.0% | 0.0% |
| city_country_currency | 4 | 0.0% | 0.0% |
| company_founder_nationality | 4 | 0.0% | 0.0% |
| product_company_country | 10 | 0.0% | 0.0% |
| scientist_discovery_field | 4 | 0.0% | 0.0% |

## Conclusion

- B fact-QA accuracy: **0.0%**.
- 80% learned-facts gate: **FAIL**.
- Conclusion: B did not learn the single-hop facts strongly enough; the repair numbers are not yet interpretable as a pure bridge/composition failure.
