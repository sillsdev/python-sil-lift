# Ficheiros de grande dimensão (transmissão em fluxo)

A função `load()` constrói todo o grafo de objetos. No caso de léxicos com várias centenas de MB, a API de streaming processa uma entrada de cada vez numa memória limitada — o mesmo tipo `Entry`, pelo que o código escrito para um dos modos funciona também no outro.

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # analisado antecipadamente (precede as entradas)
    for entry in reader:              # Iterador preguiçoso [Entry]
        ...
```

```python
com sil_lift.open_reader("big.lift") como reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) como writer:
    para cada entry em reader:
        if not entry.date_deleted:    # por exemplo, eliminar registos obsoletos
            writer.write(entry)
```

Notas:

- O resultado gerado pelo escritor é exatamente o que o serializador canónico de documento completo produziria para o mesmo conteúdo — os dois modos nunca divergem.
- O modo de transmissão contínua não reutiliza bytes da fonte: a saída é sempre canónica. Os resíduos LIFT ao nível da raiz — comentários entre entradas e atributos fora do esquema em `<lift>` — não são transportados; as entradas e o cabeçalho estão completos, incluindo os resíduos.
- Se ocorrer uma exceção no corpo de um bloco `open_writer`, o ficheiro fica visivelmente incompleto (sem o comando de fecho `</lift>`) — um léxico parcialmente escrito não deve parecer completo.
