"""
Microsserviço de Relatórios
Responsável por: geração, visualização, histórico e exclusão de relatórios
"""
from flask import render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
import json
from src.models import db, Report
from routes import routes, carbon_calculator
from routes.utils.data_extraction import extract_data_from_conversation
from routes.utils.ai_helper import generate_report_text


@routes.route("/generate_report", methods=['POST'])
@login_required
def generate_report():
    """Gera relatório de pegada de carbono"""
    from routes.chat_routes import conversation_history
    
    print("\n=== INICIANDO GERAÇÃO DE RELATÓRIO ===")
    
    # Extrair dados da conversa
    extracted_data = extract_data_from_conversation(conversation_history)
    if not extracted_data:
        return jsonify({
            "error": "Não consegui processar os dados. Use a Calculadora Manual.",
            "redirect": url_for('main.show_calculator_form')
        }), 500
    
    print(f"📊 Dados extraídos: {extracted_data}")
    
    # Calcular pegada de carbono
    try:
        calculation_results = carbon_calculator.calculate_footprint(extracted_data)
        print(f"✅ Cálculo: {calculation_results['total_kg_co2e']} kg CO2e")
    except Exception as e:
        print(f"❌ Erro no cálculo: {e}")
        return jsonify({"error": "Erro ao calcular"}), 500
    
    # Gerar relatório narrativo
    text_report = generate_report_text(calculation_results)
    
    # Salvar no banco
    try:
        new_report = Report(
            user_id=current_user.id,
            km_carro=extracted_data.get('km_carro'),
            tipo_combustivel=extracted_data.get('tipo_combustivel'),
            km_onibus=extracted_data.get('km_onibus'),
            kwh_eletricidade=extracted_data.get('kwh_eletricidade'),
            kg_gas_glp=extracted_data.get('kg_gas_glp'),
            total_kg_co2e=calculation_results['total_kg_co2e'],
            transporte_kg_co2e=calculation_results['details_kg_co2e']['transporte'],
            energia_eletrica_kg_co2e=calculation_results['details_kg_co2e']['energia_eletrica'],
            gas_cozinha_kg_co2e=calculation_results['details_kg_co2e']['gas_cozinha'],
            narrative_report=text_report
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        print(f"✅ Relatório salvo (ID: {new_report.id})\n")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao salvar: {e}")
        return jsonify({"error": "Erro ao salvar"}), 500
    
    session['report_data'] = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
        "report_id": new_report.id
    }
    
    return jsonify({"status": "success", "redirect_url": url_for('main.show_report')})


@routes.route("/report")
@login_required
def show_report():
    """Exibe relatório atual"""
    report_data = session.get('report_data')
    if not report_data:
        return redirect(url_for('main.home'))
    return render_template("calculator.html", report_data=report_data)


@routes.route('/calculator')
def show_calculator_form():
    """Exibe formulário de calculadora manual"""
    return render_template('direct_calculator.html')


@routes.route('/calculator', methods=['POST'])
@login_required
def handle_calculator_form():
    """Processa formulário da calculadora manual"""
    sanitized_data = {
        'km_carro': request.form.get('km_carro', type=float),
        'tipo_combustivel': request.form.get('tipo_combustivel'),
        'km_onibus': request.form.get('km_onibus', type=float),
        'kwh_eletricidade': request.form.get('kwh_eletricidade', type=float),
        'kg_gas_glp': (request.form.get('botijoes_gas', type=float) or 0) * 13.0
    }
    
    calculation_results = carbon_calculator.calculate_footprint(sanitized_data)
    text_report = generate_report_text(calculation_results)
    
    new_report = Report(
        user_id=current_user.id,
        **sanitized_data,
        total_kg_co2e=calculation_results['total_kg_co2e'],
        transporte_kg_co2e=calculation_results['details_kg_co2e']['transporte'],
        energia_eletrica_kg_co2e=calculation_results['details_kg_co2e']['energia_eletrica'],
        gas_cozinha_kg_co2e=calculation_results['details_kg_co2e']['gas_cozinha'],
        narrative_report=text_report
    )
    
    db.session.add(new_report)
    db.session.commit()
    
    session['report_data'] = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
        "report_id": new_report.id
    }
    
    return redirect(url_for('main.show_report'))


@routes.route('/history')
@login_required
def view_history():
    """Histórico de relatórios"""
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    return render_template('history.html', reports=reports)


@routes.route('/api/reports')
@login_required
def get_user_reports():
    """API JSON de relatórios"""
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    return jsonify([report.to_dict() for report in reports])


@routes.route('/report/<int:report_id>')
@login_required
def view_specific_report(report_id):
    """Visualiza relatório específico"""
    report = Report.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    
    report_data = {
        "data_for_dashboard": {
            'details_kg_co2e': {
                'transporte': report.transporte_kg_co2e,
                'energia_eletrica': report.energia_eletrica_kg_co2e,
                'gas_cozinha': report.gas_cozinha_kg_co2e
            },
            'total_kg_co2e': report.total_kg_co2e
        },
        "narrative_report": report.narrative_report
    }
    
    return render_template('calculator.html', report_data=report_data)


@routes.route('/report/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    """Deleta relatório"""
    report = Report.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    db.session.delete(report)
    db.session.commit()
    return jsonify({"message": "Relatório deletado"}), 200
