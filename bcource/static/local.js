let editor = undefined;

// JavaScript addEventListener for password, submit and enable form
(() => {
	//	'use strict'
	//
	//	// Fetch all the forms we want to apply custom Bootstrap validation styles to
	//
	//	// Loop over them and prevent submission
	
//	const forms = document.querySelectorAll('.needs-validation')
//	Array.from(forms).forEach(form => {
//		form.addEventListener('submit', event => {
//			console.log(event);
//			console.log("editor: " + editor);
//			if (editor) {
//				editor.updateSourceElement();
//			}
//			if (!form.checkValidity()) {
//				event.preventDefault()
//				event.stopPropagation()
//			};
//
//			event.submitter.disable = true;
//
//			form.classList.add('was-validated');
//		}, true)
//	})

	const togglePasswordbutton = document.querySelectorAll('.toggle-password');

	togglePasswordbutton.forEach(button => {
		button.addEventListener('click', (event) => {
			// toggle the input field between password and text
			const inputGroup = event.target.closest(".input-group");
			const formInputArray = inputGroup.querySelectorAll('input');
			Array.from(formInputArray).forEach((passwordField) => {
				const isPassword = passwordField.type === 'password';
				passwordField.type = isPassword ? 'text' : 'password';
			});
						
			// toggle the icon
			const elementIArray = inputGroup.querySelectorAll('i');
			Array.from(elementIArray).forEach((iElement) => {
				iElement.classList.toggle('bi-eye')
			});

		});


	})

	// check if there are any floating-alert to close with a timeout
	const alertList = document.querySelectorAll('.floating-alert-close');
	const b = jQuery('.floating-alert-close')

		const alertsAll = [...alertList].map(element => new bootstrap.Alert(element))
	i = 1
	Array.from(alertsAll).forEach((alertItem) => {
		var timeOut = alertItem._element.getAttribute('timeout');
		if (!timeOut) {
			timeOut = 4000; // default timeout
		}
		
		
		const timeOuts = timeOut * i;
		i= i + 1;

		window.setTimeout(function() {
			//alertItem.close();
			const id = alertItem._element.getAttribute("id")
			$('#' + id).slideUp()
		}, timeOuts);
	});
	
	const input = document.querySelector(".phone_number");
	if (input) {
	  const iti = window.intlTelInput(input, {
	    loadUtils: () => import("https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/js/utils.js"),
	    initialCountry: "NL",
	    nationalMode: true,
	  });
	  
	  input.form.onsubmit = () => {
		  input.setCustomValidity("");
		  if (iti.isValidNumber()){
			  input.value = iti.getNumber()
		  }	  
	  };
	};

	// Hide option from results when selected
	const selectElements = $('.select2-js');

	selectElements.each(function(i, sElement)
	{	
		const selectElement = $("#" + sElement.id)
		
		function filterSelectedOptions(option) {
		    // Return the default text for placeholders
		    if (!option.id) return option.text;

		    // Get selected values as an array
		    const selectedValues = selectElement.val() || [];

		    // Hide already selected options
		    return selectedValues.includes(option.id) ? null : option.text;
		}

		selectElement.select2({
	    	templateResult: filterSelectedOptions,
			width: "100%"
		});
	})
	
//	$('.select2-js').each(function( select_item ){
//		select_item.select2({
//	    templateResult: filterSelectedOptions
//		});
//	})	
		
})()

function encodeQueryData(data) {
   const ret = [];
   for (let d in data)
     ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
   return ret.join('&');
}

function safeConfirm(msg) {
	
    try {
        return confirm(msg) ? true : false;
    } catch (e) {
        return false;
    }
}

$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

