Registrar mapping

Source field	    Target field	    Rule	                    Reject condition
id	                student_id	        Rename, trim	            Invalid ID format
name	            full_name	        Rename, trim	            Empty name
program	            program	            Lookup/allow-list	        Unknown program
year	            year_level	        Convert/validate integer	Outside 1–4
email	            email	            Validate email	            Invalid format

Library mapping

Source field	    Target field	    Rule	                    Reject condition
borrower@id	        student_id	        Extract attribute, rename	Invalid or unknown ID
unreturned_books	Book count	        Convert to integer	        Negative or noninteger
fine	            Fine amount	        Convert to Decimal	        Invalid or negative amount
Source identity	    office	            Fixed value LIBRARY	        Wrong source
Book count + fine	status	            Calculate	                Invalid inputs
Book count + fine	reason	            Merge descriptions	        Invalid inputs

Accounting mapping

Source field	    Target field	    Rule	                    Reject condition
student_no	        student_id	        Rename, trim	            Invalid or unknown ID
balance	            Balance amount	    Convert to Decimal	        Invalid amount
Source identity	    office	            Fixed value ACCOUNTING	    Wrong source
Balance	            status	            Calculate	                Invalid balance
Balance	            reason	            Format description	        Invalid balance

Applying all transformation rules from the module

Transformation	Application in our Hub
Rename	        student_no → student_id
Split	        Separate first and last names if required by a source contract
Merge	        Combine unpaid fines and unreturned books into one reason
Change          case / trim	Normalize program codes and surrounding whitespace
Lookup	        Map program codes to program names
Reformat	    Convert agreed source dates to ISO 8601
Convert type	Convert "3" to integer 3
Default value	Missing clearance record defaults to HOLD with a reason
Calculate	    Determine office and overall clearance status
Drop	        Exclude unnecessary personal fields from reports