# Etapa 1

O objetivo da primeira etapa é adquirir alguma vivência no uso de sockets. Implemente algum protocolo qualquer de camada de aplicação usando sockets TCP ou UDP, na linguagem e na plataforma de sua escolha.

Dê preferência a algum protocolo de camada de aplicação que funcione sobre TCP, pois a próxima etapa do projeto será a implementação do TCP. Prefira também implementar algum protocolo que permita enviar grandes quantidades de dados em uma única conexão, pois isso será importante para testar o controle de fluxo e o controle de congestionamento do TCP durante a próxima etapa.

Note que usar algum programa ou biblioteca pronta não equivale a implementar um protocolo de camada de aplicação! Use diretamente a API de sockets de baixo nível disponível na sua linguagem / plataforma. Durante a aula, mostramos alguns exemplos do uso de sockets TCP em Python. Esses exemplos estão [disponíveis aqui](https://gist.github.com/thotypous/10a315490c9c16f0d648f8357e90a349).

Caso você opte por alguma plataforma que não tenha suporte nativo a sockets, por exemplo FPGA ou microcontrolador, por enquanto você pode 1) trabalhar apenas com testes unitários; 2) trabalhar com simulação e integrar sockets ao simulador; ou 3) executar sockets em um computador para emular a parte ainda inexistente do circuito, e comunicar-se com a placa de desenvolvimento por meio de algum protocolo simples. Algumas dessas estratégias são exemplificadas [neste esboço em Bluespec](https://pmatias.me/cco130/public/files/exemplos_bluespec.tar.gz).

# Etapa 2

Implemente o protocolo TCP. Para obter a nota completa, você deve implementar e exercitar (testar e comprovar que funcionam) os seguintes aspectos do protocolo TCP:

  -  Estabelecer conexão (handshake SYN, SYN+ACK, ACK) com número de sequência inicial aleatório.
  -  Transmitir e receber corretamente os segmentos.
  -  Retransmitir corretamente segmentos que forem perdidos ou corrompidos.
  -  Estimar o timeout para retransmissão de acordo com as recomendações do livro-texto ([RFC 2988](https://tools.ietf.org/html/rfc2988)).
  -  Implementar a semântica para timeout e ACKs duplos de acordo com as recomendações do livro-texto.
  -  Tratar e informar corretamente o campo window size, implementando controle de fluxo.
  -  Realizar controle de congestionamento de acordo com as recomendações do livro-texto ([RFC 5681](https://tools.ietf.org/html/rfc5681)).
  -  Fechar a conexão de forma limpa (lidando corretamente com a flag FIN).

Se você tiver adotado uma plataforma com suporte nativo a sockets, provavelmente você conseguirá utilizar algum tipo de raw socket que exponha ao espaço de usuário o pacote processado somente até a camada de rede. [Este exemplo](https://gist.github.com/thotypous/2b9587c8f14eadc8a078a237788941bb) mostra como isso pode ser feito no Linux em linguagem Python.

Nesse caso, a dica é fazer testes plugando a sua implementação de TCP a uma implementação muito simples de servidor HTTP (por exemplo, que ignore a requisição e volte sempre a mesma resposta, em uma conexão não-persistente) e utilizar um cliente pronto (por exemplo o wget) para conectar-se a ele. Volte uma resposta HTTP bastante grande, assim você pode:

  -  Testar o controle de fluxo teclando Ctrl+Z no terminal em que está executando o wget para suspendê-lo, e depois usando o comando fg para retomar a execução do processo.

  -  Testar o controle de congestionamento executando diversas instâncias do seu servidor, que escutem em portas distintas, e verificando se a banda é dividida igualmente entre os diversos clientes (wget) que se conectem a cada uma dessas portas.

Caso você tenha optado por alguma plataforma que não tenha suporte nativo a sockets, continue seguindo as mesmas orientações que foram dadas para a etapa anterior.

Sim, esta etapa é a mais complexa do projeto, por isso mesmo foram alocadas duas aulas para desenvolvimento e tira-dúvidas!

# Etapa 3

O objetivo desta etapa é trabalhar um pouco com a camada de rede. Felizmente a implementação da camada de rede em um host costuma ser bastante simples, pois geralmente ele está conectado a um único roteador, o que torna a questão do encaminhamento de pacotes (que é a tarefa mais complexa atribuída à camada de rede) um problema trivial.

Nesta etapa, vamos exercitar duas tarefas relacionadas à camada rede:

- Interpretação de cabeçalhos IP.

- Reconstrução de datagramas IP fragmentados.

O [código de exemplo](https://gist.github.com/thotypous/660caaf197146bb4b99bc007a31b6119) fornecido para esta etapa gera pings com um grande payload destinados a um endereço definido na variável dest_addr. Uma sugestão para exercitar as tarefas acima é reconstruir a resposta ao ping que chegar de volta. Preste atenção aos seguintes pontos:

- O seu código deve conseguir funcionar mesmo que os fragmentos cheguem fora de ordem.

- Você deve implementar um timeout para desistir de remontar datagramas cujos fragmentos estejam demorando muito para chegar (e provavelmente tenham sido perdidos).

Mostre na tela informações sobre os datagramas remontados.