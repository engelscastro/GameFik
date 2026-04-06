/**
 * Sistema de Menu Suspenso para Anos e Séries
 * Gamefik Academic System
 */

// Configuração dos anos e séries do sistema educacional brasileiro
const EDUCATION_LEVELS = {
    'fundamental_inicial': {
        label: 'Ensino Fundamental - Anos Iniciais',
        years: [
            { value: '1_ano_inicial', label: '1º Ano' },
            { value: '2_ano_inicial', label: '2º Ano' },
            { value: '3_ano_inicial', label: '3º Ano' },
            { value: '4_ano_inicial', label: '4º Ano' },
            { value: '5_ano_inicial', label: '5º Ano' }
        ]
    },
    'fundamental_final': {
        label: 'Ensino Fundamental - Anos Finais',
        years: [
            { value: '6_ano_final', label: '6º Ano' },
            { value: '7_ano_final', label: '7º Ano' },
            { value: '8_ano_final', label: '8º Ano' },
            { value: '9_ano_final', label: '9º Ano' }
        ]
    },
    'medio': {
        label: 'Ensino Médio',
        years: [
            { value: '1_ano_medio', label: '1º Ano' },
            { value: '2_ano_medio', label: '2º Ano' },
            { value: '3_ano_medio', label: '3º Ano' }
        ]
    }
};

/**
 * Classe para gerenciar seletores de ano/série
 */
class GradeSelector {
    constructor() {
        this.selectors = new Map();
        this.initializeStyles();
    }

    /**
     * Inicializa os estilos CSS para os seletores
     */
    initializeStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .grade-selector-container {
                margin-bottom: 20px;
            }

            .grade-selector-label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #555;
                font-size: 0.9rem;
            }

            .grade-selector-wrapper {
                position: relative;
                display: inline-block;
                width: 100%;
            }

            .grade-selector {
                width: 100%;
                padding: 12px 40px 12px 15px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 14px;
                background: #f8f9fa;
                cursor: pointer;
                transition: all 0.3s ease;
                appearance: none;
                -webkit-appearance: none;
                -moz-appearance: none;
            }

            .grade-selector:focus {
                outline: none;
                border-color: #764ba2;
                background: white;
                box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.1);
            }

            .grade-selector:hover {
                border-color: #764ba2;
                background: white;
            }

            .grade-selector-arrow {
                position: absolute;
                right: 12px;
                top: 50%;
                transform: translateY(-50%);
                pointer-events: none;
                color: #764ba2;
                font-size: 12px;
            }

            .grade-selector optgroup {
                font-weight: bold;
                color: #764ba2;
                background: #f8f9fa;
                padding: 8px;
            }

            .grade-selector option {
                padding: 8px;
                color: #333;
                background: white;
            }

            .grade-selector option:hover {
                background: #f0f0f0;
            }

            .grade-selector-multiple {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }

            @media (max-width: 768px) {
                .grade-selector-multiple {
                    grid-template-columns: 1fr;
                }
            }

            .grade-selector-info {
                background: #e8f4fd;
                border: 1px solid #bee5eb;
                border-radius: 6px;
                padding: 10px;
                margin-top: 8px;
                font-size: 0.85rem;
                color: #0c5460;
            }

            .grade-selector-info .icon {
                margin-right: 5px;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Cria um seletor de ano/série
     * @param {string} containerId - ID do container onde será inserido o seletor
     * @param {Object} options - Opções de configuração
     */
    createSelector(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} não encontrado`);
            return null;
        }

        const config = {
            id: options.id || `grade-selector-${Date.now()}`,
            label: options.label || 'Ano/Série',
            placeholder: options.placeholder || 'Selecione o ano/série',
            multiple: options.multiple || false,
            required: options.required || false,
            showInfo: options.showInfo !== false,
            onChange: options.onChange || null,
            value: options.value || null
        };

        const selectorHtml = this.generateSelectorHtml(config);
        container.innerHTML = selectorHtml;

        const selector = container.querySelector(`#${config.id}`);
        
        // Configurar evento de mudança
        if (config.onChange) {
            selector.addEventListener('change', (e) => {
                config.onChange(e.target.value, e.target);
            });
        }

        // Definir valor inicial se fornecido
        if (config.value) {
            selector.value = config.value;
        }

        // Armazenar referência
        this.selectors.set(config.id, {
            element: selector,
            config: config
        });

        return selector;
    }

    /**
     * Gera o HTML do seletor
     * @param {Object} config - Configuração do seletor
     */
    generateSelectorHtml(config) {
        const requiredAttr = config.required ? 'required' : '';
        const multipleAttr = config.multiple ? 'multiple' : '';
        
        let optionsHtml = `<option value="">${config.placeholder}</option>`;
        
        // Gerar opções agrupadas por nível de ensino
        Object.entries(EDUCATION_LEVELS).forEach(([levelKey, level]) => {
            optionsHtml += `<optgroup label="${level.label}">`;
            level.years.forEach(year => {
                optionsHtml += `<option value="${year.value}">${year.label}</option>`;
            });
            optionsHtml += `</optgroup>`;
        });

        const infoHtml = config.showInfo ? `
            <div class="grade-selector-info">
                <span class="icon">ℹ️</span>
                Sistema educacional brasileiro: Fundamental (1º-9º ano) e Médio (1º-3º ano)
            </div>
        ` : '';

        return `
            <div class="grade-selector-container">
                <label for="${config.id}" class="grade-selector-label">
                    ${config.label}${config.required ? ' *' : ''}
                </label>
                <div class="grade-selector-wrapper">
                    <select id="${config.id}" class="grade-selector" ${requiredAttr} ${multipleAttr}>
                        ${optionsHtml}
                    </select>
                    <span class="grade-selector-arrow">▼</span>
                </div>
                ${infoHtml}
            </div>
        `;
    }

    /**
     * Cria múltiplos seletores (para professores que lecionam em várias séries)
     * @param {string} containerId - ID do container
     * @param {Object} options - Opções de configuração
     */
    createMultipleSelector(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} não encontrado`);
            return null;
        }

        const config = {
            primaryId: options.primaryId || `grade-primary-${Date.now()}`,
            secondaryId: options.secondaryId || `grade-secondary-${Date.now()}`,
            primaryLabel: options.primaryLabel || 'Série Principal',
            secondaryLabel: options.secondaryLabel || 'Séries Adicionais (opcional)',
            onChange: options.onChange || null
        };

        const multipleHtml = `
            <div class="grade-selector-multiple">
                <div id="${config.primaryId}-container"></div>
                <div id="${config.secondaryId}-container"></div>
            </div>
        `;

        container.innerHTML = multipleHtml;

        // Criar seletor principal
        const primarySelector = this.createSelector(`${config.primaryId}-container`, {
            id: config.primaryId,
            label: config.primaryLabel,
            required: true,
            showInfo: false,
            onChange: config.onChange
        });

        // Criar seletor secundário (múltiplo)
        const secondarySelector = this.createSelector(`${config.secondaryId}-container`, {
            id: config.secondaryId,
            label: config.secondaryLabel,
            multiple: true,
            showInfo: true,
            onChange: config.onChange
        });

        return {
            primary: primarySelector,
            secondary: secondarySelector
        };
    }

    /**
     * Obtém o valor de um seletor
     * @param {string} selectorId - ID do seletor
     */
    getValue(selectorId) {
        const selectorData = this.selectors.get(selectorId);
        if (!selectorData) {
            console.error(`Seletor ${selectorId} não encontrado`);
            return null;
        }

        const element = selectorData.element;
        if (element.multiple) {
            return Array.from(element.selectedOptions).map(option => option.value);
        }
        return element.value;
    }

    /**
     * Define o valor de um seletor
     * @param {string} selectorId - ID do seletor
     * @param {string|Array} value - Valor(es) a serem definidos
     */
    setValue(selectorId, value) {
        const selectorData = this.selectors.get(selectorId);
        if (!selectorData) {
            console.error(`Seletor ${selectorId} não encontrado`);
            return false;
        }

        const element = selectorData.element;
        if (element.multiple && Array.isArray(value)) {
            // Limpar seleções anteriores
            Array.from(element.options).forEach(option => {
                option.selected = value.includes(option.value);
            });
        } else {
            element.value = value;
        }

        // Disparar evento de mudança
        element.dispatchEvent(new Event('change'));
        return true;
    }

    /**
     * Obtém o texto legível de um valor de série
     * @param {string} value - Valor da série
     */
    getGradeLabel(value) {
        for (const level of Object.values(EDUCATION_LEVELS)) {
            const year = level.years.find(y => y.value === value);
            if (year) {
                return `${year.label} - ${level.label}`;
            }
        }
        return value;
    }

    /**
     * Obtém todas as séries de um nível específico
     * @param {string} levelKey - Chave do nível (fundamental_inicial, fundamental_final, medio)
     */
    getGradesByLevel(levelKey) {
        return EDUCATION_LEVELS[levelKey]?.years || [];
    }

    /**
     * Valida se uma série é válida
     * @param {string} value - Valor da série
     */
    isValidGrade(value) {
        for (const level of Object.values(EDUCATION_LEVELS)) {
            if (level.years.some(y => y.value === value)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Remove um seletor
     * @param {string} selectorId - ID do seletor
     */
    removeSelector(selectorId) {
        const selectorData = this.selectors.get(selectorId);
        if (selectorData) {
            selectorData.element.remove();
            this.selectors.delete(selectorId);
            return true;
        }
        return false;
    }

    /**
     * Obtém estatísticas dos seletores criados
     */
    getStats() {
        return {
            totalSelectors: this.selectors.size,
            selectors: Array.from(this.selectors.keys())
        };
    }
}

// Instância global do seletor de séries
window.gradeSelector = new GradeSelector();

// Funções de conveniência para uso global
window.createGradeSelector = (containerId, options) => {
    return window.gradeSelector.createSelector(containerId, options);
};

window.createMultipleGradeSelector = (containerId, options) => {
    return window.gradeSelector.createMultipleSelector(containerId, options);
};

window.getGradeValue = (selectorId) => {
    return window.gradeSelector.getValue(selectorId);
};

window.setGradeValue = (selectorId, value) => {
    return window.gradeSelector.setValue(selectorId, value);
};

window.getGradeLabel = (value) => {
    return window.gradeSelector.getGradeLabel(value);
};

// Exportar para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GradeSelector, EDUCATION_LEVELS };
}
