I have some examples where users have found errors: 
"electronic funds transfer : BSB : 062-000 Account Number : 1617 8029" did not pick up the bank account. 

"Payee Name : Right2Drive Pty Ltd Claim" did not pick up the organization or business name.

"Diary Date: 13/05/2025 Diary Assigned To : Bruno Aloi Subject : Await Credit Op to place funds" did not pick up 
the NAME_CONSULTANT pattern.

A lot of things are being picked up as PERSON like "Balance Outstanding" "Await" "Repairer Unreachable" "Drop" 
"Advised" or a word is being captured after a name like "John Smith Subject" is being flagged as a PERSON when
the Subject bit should not be captured.