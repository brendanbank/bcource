// JavaScript addEventListener for password, submit and enable form
(() => {
	//	'use strict'
	//
	//	// Fetch all the forms we want to apply custom Bootstrap validation styles to
	const forms = document.querySelectorAll('.needs-validation')
	//
	//	// Loop over them and prevent submission
	Array.from(forms).forEach(form => {
		form.addEventListener('submit', event => {
			if (!form.checkValidity()) {
				event.preventDefault()
				event.stopPropagation()
			};

			console.log(event);
			event.submitter.disable = true;

			form.classList.add('was-validated');
		}, true)
	})

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
	const alertsAll = [...alertList].map(element => new bootstrap.Alert(element))

	Array.from(alertsAll).forEach((alertItem) => {
		var timeOut = alertItem._element.getAttribute('timeout');
		if (!timeOut) {
			timeOut = 2000; // default timeout
		}
		const timeOuts = timeOut;

		window.setTimeout(function() {
			alertItem.close();
		}, timeOuts);
	});

})()
