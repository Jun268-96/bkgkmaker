# Platform CSV formats

Use UTF-8 with BOM and CRLF line endings. Preserve embedded newlines and commas through CSV quoting.

The harness also enforces fixed column counts, byte-level BOM and record separators, correct-answer mapping, control-character rejection, formula-injection protection, and round-trip parsing. A passing result means structurally import-ready; it does not mean a live platform upload was performed.

## Gimkit

Row 1: `Gimkit Spreadsheet Import Template`

Row 2 columns A–E:

1. `Question`
2. `Correct Answer`
3. `Incorrect Answer 1`
4. `Incorrect Answer 2 (Optional)`
5. `Incorrect Answer 3 (Optional)`

Write data from row 3. Put the correct answer text in column B. Require at least one incorrect answer.

Official import guide:
https://help.gimkit.com/en/article/create-a-kit-with-a-csv-file-wv72i9/

## Blooket

Row 1: `Blooket\nImport Template`

Row 2 columns A–H:

1. `Question #`
2. `Question Text`
3. `Answer 1`
4. `Answer 2`
5. `Answer 3\n(Optional)`
6. `Answer 4\n(Optional)`
7. `Time Limit (sec)\n(Max: 300 seconds)`
8. `Correct Answer(s)\n(Only include Answer #)`

Write data from row 3. Store only the 1-based answer position in column H. Balance correct positions across the set. Enforce 5–300 seconds and a maximum of 100 questions for this skill.

Official import guide:
https://help.blooket.com/hc/en-us/articles/16002377931543-How-to-Import-Questions-from-a-Spreadsheet-into-Blooket
