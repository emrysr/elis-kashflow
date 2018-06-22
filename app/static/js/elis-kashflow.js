// HAD TO CHANGE THE {{ }} VARIABLE DELIMITER TO NOT MESS UP JINJA
// variables changed in vue from {{name}} to ${name}

/**
* upload form to supply invoice to rossum's elis service
*/
// please translate these if you can
const messages = {
    zh : {
        'Error uploading! Try another': '上传时出错！尝试另一个'
    },
    cy : {
        'Error uploading! Try another': 'Rhowch gynnig arall'
    }
}


// Create VueI18n instance with options
const i18n = new VueI18n({
    locale: 'en', // set locale
    messages, // set locale messages
    //fallbackLocale: 'en'
})


var upload = new Vue({
    i18n: i18n,
    el: '#upload-new',
    delimiters: ['${','}'],//stop vue from clashing with jinja
    data: {
        status: 'ready',
        isDroppable: false,
        file: false,
        errors: [],
        responses: [],
        invoice: {},
        errorTimeout: 2200,
        timeout: null,
        wait: false
    },
    computed: {
        fileName: function(){
            return !this.file ? "(or drag 'n drop)" : this.file.name
        },
        fileSize: function(){
            return !this.file ? '' : Number(this.file.size/1000).toFixed(2)+ 'KB'
        },
        fileType: function(){
            return !this.file ? '' : this.file.type
        }
    },
    methods: {
        drop: function(event) {
            this.isDroppable = false
            this.$refs.file.files = event.dataTransfer.files
            this.$refs.file.form.dispatchEvent(new Event('change'))
        },
        sendFile: function(event) {
            console.log('sendFile')
            this.file = this.$refs.file.files[0]
            let formData = new FormData()
            this.status = 'loading'
            vm = this
            fetch('invoices', {
                method: 'POST',
                body: formData
            })
            .then(function(response) {
                vm.status = 'ready'
                if (!response.ok) {
                    throw Error("Unexpected Response: ", response.statusText)
                }
                return response.json()
            })
            .then(function(json) {
                //POST success read result
                vm.responses.push(json);
                this.status = 'success'
                vm.notify()
                //Place result into table
                vm.invoice = {}
            })
            .catch((response) => {
                vm.errors.push(response)
                this.status = 'error'
                vm.notify()
                console.log(response)
            })
        },
        notify: function() {
            let vm = this

            // repeat
            let notifyTimer = setInterval(function(){
                if(vm.wait) {
                    clearInterval(notifyTimer)
                    return false
                }
                vm.file = false
                vm.status = 'ready'
            }, vm.errorTimeout)

            // clear interal after 3
            setTimeout(function() {
                clearInterval(notifyTimer)
                vm.file = false
                vm.status = 'ready'
            }, vm.errorTimeout*2)
        }
    }
})


/**
* list of uploaded pdfs vs the list of raised purchase orders
*/
var list = new Vue({
    el: '#invoices',
    delimiters: ['${','}'],
    data: {
        status: 'ready',
        invoices: [],
    },
    methods: {
        sync: function(event){
            this.status = 'loading'
            event.target.blur()
            event.preventDefault()
            this.getInvoices()
        },
        getInvoices: function(){
            let vm = this;
            fetch('/invoices')
            .then(function(response) {
                return response.json()
            })
            .then(function(json) {
                vm.invoices = json.data
                vm.status = 'ready'
            })
            .catch(function(response){
                vm.status = 'error'
                console.log('Error: ',response)
            })
        }
    }
})


/**
* footer options
*/
var footer = new Vue({
    el: '#footer',
    delimiters: ['${','}'],
    data: {
        status2: upload.status,
        status: 'you dude',
    }
})