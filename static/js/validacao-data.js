/**
 * Validação de datas no formato brasileiro (dd/mm/aaaa)
 */

// Função para validar data no formato dd/mm/aaaa
function validarDataBrasileira(data) {
    // Regex para formato dd/mm/aaaa
    const regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
    const match = data.match(regex);
    
    if (!match) {
        return false;
    }
    
    const dia = parseInt(match[1], 10);
    const mes = parseInt(match[2], 10);
    const ano = parseInt(match[3], 10);
    
    // Verificar se é uma data válida
    const dataObj = new Date(ano, mes - 1, dia);
    
    return dataObj.getFullYear() === ano &&
           dataObj.getMonth() === mes - 1 &&
           dataObj.getDate() === dia &&
           ano >= 1900 && ano <= 2100;
}

// Função para adicionar validação aos campos de data
function adicionarValidacaoData() {
    const camposData = document.querySelectorAll('input[name="data_nascimento"]');
    
    camposData.forEach(campo => {
        campo.addEventListener('blur', function() {
            const valor = this.value.trim();
            
            if (valor && !validarDataBrasileira(valor)) {
                this.setCustomValidity('Data inválida. Use o formato dd/mm/aaaa');
                this.style.borderColor = '#dc3545';
            } else {
                this.setCustomValidity('');
                this.style.borderColor = '';
            }
        });
        
        // Limpar validação ao digitar
        campo.addEventListener('input', function() {
            this.setCustomValidity('');
            this.style.borderColor = '';
        });
    });
}

// Inicializar validação quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    adicionarValidacaoData();
    
    // Validação no envio do formulário
    const formularios = document.querySelectorAll('form');
    
    formularios.forEach(form => {
        form.addEventListener('submit', function(e) {
            const camposData = this.querySelectorAll('input[name="data_nascimento"]');
            let temErro = false;
            
            camposData.forEach(campo => {
                const valor = campo.value.trim();
                
                if (valor && !validarDataBrasileira(valor)) {
                    campo.setCustomValidity('Data inválida. Use o formato dd/mm/aaaa');
                    campo.style.borderColor = '#dc3545';
                    temErro = true;
                }
            });
            
            if (temErro) {
                e.preventDefault();
                alert('Por favor, corrija os erros nos campos de data antes de continuar.');
            }
        });
    });
});