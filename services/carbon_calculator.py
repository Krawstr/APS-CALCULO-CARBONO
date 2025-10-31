EMISSION_FACTORS = {
    "gasolina": 0.231,  
    "etanol": 0.095,   
    "diesel": 0.265,   
    "onibus_urbano": 0.101, 
    
    "eletricidade": 0.072, 
    "gas_glp": 3.01,      
}

def calculate_footprint(data):
    emissions = {
        "transporte": 0.0,
        "energia_eletrica": 0.0,
        "gas_cozinha": 0.0,
    }

    if data.get("km_carro") and data.get("tipo_combustivel"):
        fuel_factor = EMISSION_FACTORS.get(data["tipo_combustivel"], 0)
        emissions["transporte"] += data["km_carro"] * fuel_factor
        
    if data.get("km_onibus"):
        emissions["transporte"] += data["km_onibus"] * EMISSION_FACTORS["onibus_urbano"]

    if data.get("kwh_eletricidade"):
        emissions["energia_eletrica"] = data["kwh_eletricidade"] * EMISSION_FACTORS["eletricidade"]
        
    if data.get("kg_gas_glp"):
        emissions["gas_cozinha"] = data["kg_gas_glp"] * EMISSION_FACTORS["gas_glp"]

    total_emissions = sum(emissions.values())

    return {
        "details_kg_co2e": {k: round(v, 2) for k, v in emissions.items()},
        "total_kg_co2e": round(total_emissions, 2)
    }