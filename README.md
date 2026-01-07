Please read the text document below to activate python 3.11
<br/>
[pythondownloadinstruction.txt](https://github.com/user-attachments/files/24467423/pythondownloadinstruction.txt)​<br/>
Install the text file <br/>
[requirements.txt](https://github.com/user-attachments/files/24467460/requirements.txt) <br/>
--- 
# Guidelines: 

--- 

Create Adobe Account(each account only have 500 uses per month)<br/>
Go to https://developer.adobe.com/document-services/apis/pdf-services/#
<img width="1887" height="590" alt="image" src="https://github.com/user-attachments/assets/4a6008d5-b289-4e0a-b81e-ceae3266d552" />

# Create Credentials 

--- 

<img width="1381" height="759" alt="image" src="https://github.com/user-attachments/assets/31e7b07d-3ca2-4622-9325-1139ddf0169c" /> <br/>
when create credentials , name your Credentials Name , and tick By creating credentials, you are agreeing to our developer terms. <br/>
Once it is finalized , press the Create credentials button <br/> <br/>
This is personal info step: <br/>
<img width="634" height="499" alt="image" src="https://github.com/user-attachments/assets/f4c47d6d-780d-4cf6-b82c-47a3379bb86a" /><br/>
with cilent secret <br/>
<img width="650" height="439" alt="image" src="https://github.com/user-attachments/assets/1eb4335a-379d-4e72-b4ae-203c9c44bd8c" /><br/>
# $${\color{red} Warning&nbsp;&nbsp;&nbsp;&nbsp;:&nbsp;&nbsp;Please&nbsp;keep&nbsp;this&nbsp;personally&nbsp;for&nbsp;your&nbsp;own&nbsp;use}$$

--- 

After you create the API please follow the command or fill in the set_adobe_pdf_env.ps1 <br />
$env:PDF_SERVICES_CLIENT_ID = "PASTE_CLIENT_ID_HERE" <br/>
$env:PDF_SERVICES_CLIENT_SECRET = "PASTE_CLIENT_SECRET_HERE" <br/>
$env:PDF_SERVICES_ORG_ID = "PASTE_ORGANIZATION_ID_HERE" <br/>
After filling run the script .\set_adobe_pdf_env.ps1(from AutocadPDFconvert folder)

--- 

# Command: 
setx PDF_SERVICES_CLIENT_ID "PASTE_CLIENT_ID_HERE"  <br/>
setx PDF_SERVICES_CLIENT_SECRET "PASTE_CLIENT_SECRET_HERE"  <br/>
setx PDF_SERVICES_ORG_ID "PASTE_ORGANIZATION_ID_HERE"  <br/>
<br/>For double checking test run <br/>
echo $env:PDF_SERVICES_CLIENT_ID <br/>
echo $env:PDF_SERVICES_CLIENT_SECRET <br/>
echo $env:PDF_SERVICES_ORG_ID <br/>
it will show cilent id , cilent secret and org ID in the powershell which operate my python file 

---  

After all these procedures , cd dwgplotter to the react folder and run npm run dev

---

Once you are in the website as localhost domain below <br/>
 <img width="944" height="396" alt="image" src="https://github.com/user-attachments/assets/ba091b14-44e7-4b69-abc9-fddd38dfaca5" /><br/>
 Press Choose Files

 
 # Files Explorer Directory
 
 ---
 
 <img width="937" height="523" alt="image" src="https://github.com/user-attachments/assets/80249948-8f57-4c70-a6e8-ad142bce99bc" /><br/>
 Once you see the files explorer directory , choose the folder and press upload.(make sure the folder must have pdf files , otherwise it cannot work)<br/>
<img width="932" height="379" alt="image" src="https://github.com/user-attachments/assets/6a9429d8-656c-4901-a879-62c52360d2c3" /><br/>
<br/>
 Once you finalize the Folder that you want to convert , Press Convert Button and let it run by itself<br/> <br/>
# Minimized:

--- 

<img width="933" height="562" alt="image" src="https://github.com/user-attachments/assets/94deacdf-913b-42ef-b8d5-5f79acbbdd5c" />

# Maximize:

--- 

<img width="883" height="281" alt="image" src="https://github.com/user-attachments/assets/743c7228-66c7-41a2-8dad-804e71d09b1b" /> <br/>
<img width="883" height="832" alt="image" src="https://github.com/user-attachments/assets/0e728b22-93a0-40de-911e-f50f42bc107e" /> <br/>
<br/>
Once all the files are finished , press the download button for serperate document or Download & merged for both seperated and merged document(all drawings in one document). <br/>

 

 




