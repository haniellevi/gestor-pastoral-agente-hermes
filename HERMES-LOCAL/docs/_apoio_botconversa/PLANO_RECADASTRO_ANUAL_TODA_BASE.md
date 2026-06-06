# Plano de Recadastro Anual - Toda a Base

Data: 2026-06-05  
Base consultada no BotConversa: 84 contatos  
Status: plano operacional para executar sem abandonar a Fase 3 Hermes 2.0

Este plano existe para rodar o recadastro com toda a base de contatos de forma controlada, sem quebrar o atendimento normal e sem depender de memoria humana.

---

## 1. Decisao

Vamos rodar o recadastro anual, mas nao como disparo cego para todos de uma vez.

Modelo correto:

```text
Preparar tags/campos/sequencia
-> testar com poucos contatos
-> validar webhook e dashboard
-> enviar em ondas
-> acompanhar pendentes
-> retomar quem nao respondeu
```

Motivo: recadastro mexe com dados pessoais, pode gerar muitas respostas simultaneas e precisa respeitar opt-in/qualidade do WhatsApp.

---

## 2. Pre-requisitos antes de disparar

### BotConversa

- [ ] Criar etiqueta `Atualização Recusada`.
- [ ] Criar sequencia `SEQ - Recadastro Anual`.
- [ ] Criar sequencia `SEQ - Retomar Atualizacao Cadastral`.
- [ ] Revisar fluxo `4- Recadastro Anual`.
- [ ] Revisar fluxo `3- Atualização Cadastral`.
- [ ] Garantir que `4- Recadastro Anual` chama `POST /webhook/botconversa`.
- [ ] Garantir que `3- Atualização Cadastral` chama `POST /webhook/botconversa`.
- [ ] Parar de usar `SEQ - Revisao Cadastral 6M`.
- [ ] Parar de aplicar `Revisao 6M Agend`.

### Hermes 2.0

- [ ] Rodar migration `supabase/migrations/20260605143000_hermes_v2_mvp.sql` no Supabase de producao.
- [ ] Confirmar que `https://api.filadelfiacorrente.com/health` retorna `hermes_v2 = enabled`.
- [ ] Testar `POST /webhook/botconversa` com `tipo_evento = cadastro`.
- [ ] Conferir no dashboard v2 se entrou em `inbox_pastoral`.

---

## 3. Publico da campanha

Base atual no BotConversa: 84 contatos.

Publico inicial:

- contatos com etiqueta `Membro`;
- contatos com `Cadastro_Incompleto`;
- contatos com `Atualização Pendente`;
- contatos sem `Ultima_Atualiza_Cad`;
- contatos com `Proxima_Atualiza_Cad` vencida ou vazia.

Nao enviar nesta primeira rodada:

- contatos com `Atend Humano Ativo`;
- contatos com `Humano Necessario`;
- contatos marcados como visitante sem vinculo pastoral claro;
- contatos que recusarem atualizacao;
- contatos sem opt-in/relacao clara com a igreja, se houver duvida.

---

## 4. Mensagem recomendada

Usar tom de utilidade/atendimento, sem linguagem promocional.

Mensagem inicial:

```text
Olá, paz do Senhor! Aqui é a equipe da Igreja Batista Filadélfia Internacional de Corrente.

Estamos atualizando o cadastro pastoral da igreja para manter nossos contatos, célula e acompanhamento em ordem.

Você pode confirmar se seus dados continuam iguais ou atualizar alguma informação?
```

Botoes:

- `Tudo igual`
- `Atualizar dados`
- `Agora não`

Mensagem de privacidade curta, se couber no fluxo:

```text
Usaremos essas informações apenas para organização pastoral, contato da igreja e acompanhamento ministerial.
```

---

## 5. Fluxo `4- Recadastro Anual`

### Entrada

Pode entrar por:

- sequencia `SEQ - Recadastro Anual`;
- botao da Rute;
- filtro manual de contatos no BotConversa.

### Blocos

1. **Mensagem inicial**
   - Enviar o texto recomendado acima.
2. **Botoes**
   - `Tudo igual`
   - `Atualizar dados`
   - `Agora não`
3. **Tudo igual**
   - Aplicar `Cadastro Confirmado`.
   - Aplicar `Cadastro Completo`.
   - Remover `Atualização Pendente`.
   - Remover `Cadastro_Incompleto`.
   - Salvar `Status_Cadastro = Completo`.
   - Salvar `Ultima_Atualiza_Cad = data atual`.
   - Salvar `Proxima_Atualiza_Cad = data atual + 1 ano`.
   - Chamar webhook v2 com `tipo_evento = cadastro`.
   - Conectar em `0000 - Encerrar Conversa`.
4. **Atualizar dados**
   - Aplicar `Atualização Pendente`.
   - Salvar `Ultima_Intencao = Atualizacao_Cadastral`.
   - Conectar em `3- Atualização Cadastral`.
5. **Agora não**
   - Aplicar `Atualização Pendente`.
   - Salvar `Status_Cadastro = Atualizar depois`.
   - Inscrever em `SEQ - Retomar Atualizacao Cadastral`.
   - Chamar webhook v2 com `tipo_evento = cadastro`.
   - Conectar em `0000 - Encerrar Conversa`.
6. **Recusou**
   - Aplicar `Atualização Recusada`.
   - Remover `Atualização Pendente`.
   - Salvar `Status_Cadastro = Recusou`.
   - Chamar webhook v2 com `tipo_evento = cadastro`.
   - Conectar em `0000 - Encerrar Conversa`.

---

## 6. Payload do webhook para recadastro

Usar no fluxo `4- Recadastro Anual`:

```json
{
  "event_id": "{{subscriber.id}}-recadastro-anual-{{date.now}}",
  "subscriber_id": "{{subscriber.id}}",
  "nome": "{{subscriber.name}}",
  "telefone": "{{subscriber.phone}}",
  "mensagem": "{{last_input}}",
  "fluxo_origem": "4- Recadastro Anual",
  "tipo_evento": "cadastro",
  "campos": {
    "Status_Cadastro": "{{custom_field.Status_Cadastro}}",
    "Tipo_Vinculo": "{{custom_field.Tipo_Vinculo}}",
    "Ultima_Atualiza_Cad": "{{custom_field.Ultima_Atualiza_Cad}}",
    "Proxima_Atualiza_Cad": "{{custom_field.Proxima_Atualiza_Cad}}",
    "Ultima_Intencao": "{{custom_field.Ultima_Intencao}}",
    "Resumo_Atend_IA": "{{custom_field.Resumo_Atend_IA}}"
  }
}
```

Usar no fluxo `3- Atualização Cadastral`:

```json
{
  "event_id": "{{subscriber.id}}-atualizacao-cadastral-{{date.now}}",
  "subscriber_id": "{{subscriber.id}}",
  "nome": "{{subscriber.name}}",
  "telefone": "{{subscriber.phone}}",
  "mensagem": "{{last_input}}",
  "fluxo_origem": "3- Atualização Cadastral",
  "tipo_evento": "cadastro",
  "campos": {
    "Data_Nascimento": "{{custom_field.Data_Nascimento}}",
    "Bairro": "{{custom_field.Bairro}}",
    "Tempo_Igreja": "{{custom_field.Tempo_Igreja}}",
    "Lider_Celula": "{{custom_field.Lider_Celula}}",
    "Celula_Atual": "{{custom_field.Celula_Atual}}",
    "G12_Pastoral": "{{custom_field.G12_Pastoral}}",
    "Fez_Encontro": "{{custom_field.Fez_Encontro}}",
    "Universidade_Vida": "{{custom_field.Universidade_Vida}}",
    "Capacitacao_Destino": "{{custom_field.Capacitacao_Destino}}",
    "Ministerios": "{{custom_field.Ministerios}}",
    "Interesse_Ministerio": "{{custom_field.Interesse_Ministerio}}",
    "Status_Cadastro": "{{custom_field.Status_Cadastro}}",
    "Resumo_Atend_IA": "{{custom_field.Resumo_Atend_IA}}"
  }
}
```

---

## 7. Envio em ondas

Nao enviar para os 84 contatos de uma vez na primeira execucao.

Ordem:

1. **Teste interno**
   - 3 a 5 contatos da equipe.
   - Validar botoes, campos, webhook e dashboard.
2. **Piloto**
   - 10 contatos reais.
   - Aguardar pelo menos algumas horas e observar respostas.
3. **Onda 1**
   - 25 contatos.
4. **Onda 2**
   - 25 contatos.
5. **Onda final**
   - restante da base.

Se houver erro, parar a onda seguinte ate corrigir.

---

## 8. Indicadores para acompanhar

No dashboard Hermes 2.0:

- total de entradas `tipo_evento = cadastro`;
- quantos confirmaram sem alteracao;
- quantos foram para atualizacao completa;
- quantos ficaram pendentes;
- quantos recusaram;
- quantos precisaram de humano;
- erros de webhook.

No BotConversa:

- quantidade com `Cadastro Completo`;
- quantidade com `Atualização Pendente`;
- quantidade com `Cadastro_Incompleto`;
- quantidade com `Atualização Recusada`;
- qualidade/entrega da sequencia.

---

## 9. Regra de seguranca pastoral e operacional

- Nao pedir informacao sensivel desnecessaria.
- Nao pedir documento pessoal por WhatsApp nesta fase.
- Nao tratar aconselhamento dentro do fluxo de recadastro.
- Se a pessoa mencionar crise, dor profunda, conflito grave ou pedido pastoral, sair do recadastro e conectar em `13 - Atendimento Humano`.
- Se a pessoa pedir para nao receber mensagens, registrar e nao insistir.

---

## 10. Proxima acao

1. Criar `SEQ - Recadastro Anual`.
2. Revisar `4- Recadastro Anual` com os blocos deste documento.
3. Fazer teste interno com 3 a 5 contatos.
4. Confirmar no dashboard v2.
5. So depois iniciar piloto com 10 contatos.

