# Ficheiros de grande dimensão (transmissão em fluxo)

A função `load()` constrói todo o grafo de objetos. No caso de léxicos com várias centenas de MB, a API de streaming processa uma entrada de cada vez numa memória limitada. Retorna o mesmo tipo `Entry`, pelo que o código escrito para um dos modos funciona no outro.

## Leitura

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # analisado antecipadamente (precede as entradas)
    for entry in reader:              # Iterador preguiçoso [Entry]
        ...
```

## Escrita

```python
com sil_lift.open_reader("big.lift") como reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) como writer:
    para cada entrada em reader:
        if not entry.date_deleted:    # por exemplo, ignorar entradas marcadas como eliminadas
            writer.write(entry)
```

Notas:

- O resultado gerado pelo escritor corresponde exatamente ao que o serializador canónico de documentos completos produziria para o mesmo conteúdo; os dois modos nunca divergem.
- O modo de transmissão contínua não reutiliza bytes da fonte: a saída é sempre canónica. Os resíduos LIFT ao nível da raiz (comentários entre entradas e atributos fora do esquema em `<lift>`) são eliminados, mas as entradas e o cabeçalho mantêm os seus próprios resíduos.
- Ao contrário do [`Lexicon.save()`](../fidelity.md#saving-an-edited-document), o modo de streaming não gera marcas temporais. Uma entrada é gravada com as datas que já possui: um «streaming pass» nunca vê o documento tal como ele era, pelo que não consegue identificar quais as entradas que alterou. Defina manualmente `entry.date_modified` nos registos que esta passagem reescreve.
- Se ocorrer uma exceção no corpo de um bloco `open_writer`, o ficheiro fica visivelmente incompleto (sem o `</lift>` de fecho). Isto evita que um léxico incompleto pareça completo.
