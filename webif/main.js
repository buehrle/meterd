function disableenter() {
    var inputs = document.getElementsByTagName('input');
    var notTheseInputs = ['checkbox', 'radio', 'submit', 'reset', 'button'];
    for (input of inputs) {
        if (notTheseInputs.indexOf(input.type) === -1) {
            input.addEventListener('keypress', (e)=> {
                if (e.key === 'Enter') {
                    e.preventDefault();
                }
            })
        }
    }
}

function setvisibility(protocol) {
    var elementlist = document.querySelectorAll(".singlesetting, .registers, .datarecords");

    for (i = 0; i < elementlist.length; i++) {
        elementlist[i].classList.remove("hidden");
    }

    document.getElementById("submit-save").removeAttribute("disabled")

    if (protocol === 1) {
        elementlist = document.querySelectorAll(".device, .baudrate, .parity, .echo, .datarecords");
    } else if (protocol === 2) {
        elementlist = document.querySelectorAll(".address, .echo, .datarecords");
    } else if (protocol === 3) {
        elementlist = document.querySelectorAll(".address, .regoffset, .registers");
    }

    for (i = 0; i < elementlist.length; i++) {
        elementlist[i].classList.add("hidden");
    }
}

function askforname() {
    var tpid = prompt("Neue TPID:");

    if (tpid !== "" && tpid !== null) {
        document.getElementById("copy-tpid-hidden").value = tpid;
        document.forms["device-form"].submit();
    }
}