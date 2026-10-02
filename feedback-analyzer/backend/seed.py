"""Popula o banco com comentários de exemplo: python seed.py"""
from app.db import Base, SessionLocal, engine
from app.main import analyze_and_save

SAMPLES = [
    "A entrega chegou super rápida, embalagem impecável.",
    "Demorou três semanas para entregar e ninguém me avisou do atraso.",
    "O atendimento foi excelente, a atendente resolveu tudo em minutos.",
    "Atendimento péssimo, fiquei uma hora esperando no chat.",
    "Preço justo pela qualidade, recomendo.",
    "Muito caro para o que oferece, esperava mais.",
    "O aplicativo trava toda hora, impossível finalizar a compra.",
    "App intuitivo e rápido, gostei muito da nova versão.",
    "Produto veio com defeito e a troca foi burocrática.",
    "Qualidade do produto surpreendente, material resistente.",
    "A entrega atrasou mas o suporte me deu um desconto, fiquei satisfeito.",
    "Suporte demorou a responder, mas resolveu o problema.",
    "O site é lento e o checkout dá erro no cartão.",
    "Ótimo custo-benefício, preço abaixo da concorrência.",
    "Entrega no prazo e produto exatamente como na foto.",
    "Não recomendo, o produto quebrou em uma semana.",
    "Atendimento educado e rápido, nota dez.",
    "O aplicativo é confuso, não achei onde acompanhar meu pedido.",
    "Frete caro demais e a entrega ainda atrasou.",
    "Produto ok, nada demais. Chegou conforme o esperado.",
    "Equipe de suporte atenciosa, resolveram meu pedido de reembolso.",
    "Qualidade ruim, o acabamento deixa a desejar.",
    "Gostei do preço e da facilidade de pagar pelo app.",
    "Pedi troca e ninguém retornou meu contato até hoje.",
]

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        rows = analyze_and_save(db, SAMPLES, "seed")
    print(f"{len(rows)} comentários analisados e salvos.")
