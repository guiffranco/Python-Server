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
     cd etapa1/
     python3 cli.py
  ```

O código do cliente permite que seja enviado um arquivo .txt. Para facilitar o teste de envio de grandes quantidades de dados, o diretório da etapa já contém um arquivo chamado "input.txt", que contém 16385 bytes em caracteres "A".

## Etapa 2

Para esta etapa foi implementado, sobre um [código](https://gist.github.com/thotypous/6b4bcff336e307e4a64622aa19d4b65c "HTTP burro") básico disponibilizado pelo professor Paulo Matias, características de um TCP, como os Handshakes inicial e final, transmissão correta de segmentos, controle de congestionamento e retransmissão após timeout.

Para rodar o script em um terminal:

```bash
    cd etapa2/
    python3 serv.py
```

Em outro terminal, rodar o script:

```bash
wget localhost:7000
```

Gerando, ao fim, um arquivo index.html com a mensagem enviada ao cliente.

## Etapa 3

Para esta etapa foi implementado, sobre um [exemplo](https://gist.github.com/thotypous/660caaf197146bb4b99bc007a31b6119) disponibilizado pelo professor Paulo Matias, a interpretação de cabeçalho IP e a reconstrução de datagramas IP fragmentados (mesmo com os fragmentos chegando fora de ordem), assim como o timeout sobre esses datagramas (caso os fragmentos não se completem dentro de determinado tempo).
