# Python Server

Simple socket server in Python

## Etapa 1

Para esta etapa, foi implementado um protocolo onde:
- O cliente deseja enviar uma mensagem ao servidor. O cliente deve informar ao servidor o tamanho da mensagem que deseja-se enviar. Logo após o envio desta informação, o cliente envia a mensagem e aguarda uma resposta de recebimento do servidor.
- O servidor por sua vez aguarda uma primeira mensagem que deve conter o tamanho da "mensagem real" que o cliente deseja enviar. Ao receber estes dados o servidor se prepara para receber esta mensagem. Ele verifica se todos os dados foram recebidos, e caso obtenha sucesso, envia uma mensagem de confirmação ao cliente.

Para testar, rodar o script do servidor em um terminal:

  ```bash
     cd etapa1
     python3 serv.py
  ```
Em outro terminal, rodar o script do client:

  ```bash
     cd etapa1
     python3 cli.py
  ```

O código do cliente permite que seja enviado um arquivo .txt. Para facilitar o teste de envio de grandes quantidades de dados, o diretório da etapa já contém um arquivo chamado "input.txt", que contém 16385 bytes em caracteres "A".
