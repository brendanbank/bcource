	

'use strict'

const postal_code_field  = document.querySelector("#postal_code");
const house_number_field  = document.querySelector("#house_number");
console.log(postal_code_field)



async function fetchAddress (event) {
	
	
	const postcodeRegex = /^\d{4}\s*[a-zA-Z]{2}$/;
	const huisnummerRegex = /^\d+$/;
	
	if ( postal_code_field.value.match(postcodeRegex) == null){
		return
	}

	if ( house_number_field.value.match(huisnummerRegex) == null){
		return
	}

	
	
	
	const csrf = document.querySelector("meta[name='csrf-token']");
	
	const adress_request = new Request("/api/address", {
	  method: "POST",
	  body: "postcode="+postal_code_field.value+"&"+"huisnummer="+house_number_field.value,
	  headers: {
	    "Content-type": "application/x-www-form-urlencoded",
		'X-CSRF-TOKEN': csrf.content
	  }
	});
	
	let adress_response
	
	try {
		adress_response = await fetch(adress_request);
	} catch (error) {
		console.log(error);
	}
	const adress_obj = await adress_response.json();
	
	if (adress_obj && adress_obj.status  == 200) {
		console.log(adress_obj)

		document.querySelector("#street").value = adress_obj.straat;
		document.querySelector("#city").value = adress_obj.woonplaats;
		postal_code_field.value = adress_obj.postcode;
		
	}
}

postal_code_field.addEventListener("change", fetchAddress)
postal_code_field.addEventListener("keyup", fetchAddress)
house_number_field.addEventListener("change", fetchAddress)
house_number_field.addEventListener("keyup", fetchAddress)
