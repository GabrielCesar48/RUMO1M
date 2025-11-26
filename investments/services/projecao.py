from decimal import Decimal

def projetar_futuro(valor_atual, aumento_anual, meses, ipca_dict=None):
    valor = Decimal(str(valor_atual))
    aumento = Decimal(str(aumento_anual)) / 100

    for n in range(meses):
        # Se veio dict do BCB, extrai o valor correto
        if isinstance(ipca_dict, dict):
            ipca = Decimal(str(ipca_dict.get("valor", 0))) / 100
        else:
            ipca = Decimal(str(ipca_dict)) / 100 if ipca_dict else Decimal("0")

        valor *= (1 + aumento + ipca)

    return float(valor)
