# estadisticas.py
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import calendar

# Crear blueprint para estadísticas
estadisticas_bp = Blueprint('estadisticas', __name__)

def init_estadisticas(db, Factura, DetalleFactura, Producto):
    """
    Inicializar el blueprint con las dependencias necesarias
    
    Args:
        db: Instancia de SQLAlchemy
        Factura: Modelo de Factura
        DetalleFactura: Modelo de DetalleFactura  
        Producto: Modelo de Producto
    """
    
    @estadisticas_bp.route('/api/estadisticas_ventas')
    def estadisticas_ventas():
        try:
            # Obtener parámetros
            ano = request.args.get('ano', datetime.now().year, type=int)
            
            # Consulta para ventas por mes del año especificado
            ventas_mensuales = db.session.query(
                extract('month', Factura.fecha).label('mes'),
                func.count(Factura.id).label('cantidad_ventas'),
                func.sum(Factura.total).label('total_ventas'),
                func.avg(Factura.total).label('promedio_venta')
            ).filter(
                extract('year', Factura.fecha) == ano,
                Factura.estado != 'cancelada'
            ).group_by(
                extract('month', Factura.fecha)
            ).order_by('mes').all()
            
            # Crear estructura de datos completa (todos los 12 meses)
            datos_mensuales = []
            ventas_dict = {v.mes: v for v in ventas_mensuales}
            
            for mes in range(1, 13):
                venta_mes = ventas_dict.get(mes)
                datos_mensuales.append({
                    'mes': mes,
                    'nombre_mes': calendar.month_name[mes],
                    'nombre_corto': calendar.month_abbr[mes],
                    'cantidad_ventas': int(venta_mes.cantidad_ventas) if venta_mes else 0,
                    'total_ventas': float(venta_mes.total_ventas) if venta_mes else 0.0,
                    'promedio_venta': float(venta_mes.promedio_venta) if venta_mes else 0.0
                })
            
            # Estadísticas generales del año
            total_ano = sum(m['total_ventas'] for m in datos_mensuales)
            total_ventas_ano = sum(m['cantidad_ventas'] for m in datos_mensuales)
            promedio_mensual = total_ano / 12 if total_ano > 0 else 0
            
            # Mes con mayores ventas
            mes_mayor = max(datos_mensuales, key=lambda x: x['total_ventas'])
            mes_menor = min(datos_mensuales, key=lambda x: x['total_ventas'])
            
            # Comparación con año anterior
            ano_anterior = ano - 1
            total_ano_anterior = db.session.query(
                func.sum(Factura.total)
            ).filter(
                extract('year', Factura.fecha) == ano_anterior,
                Factura.estado != 'cancelada'
            ).scalar() or 0
            
            crecimiento = 0
            if total_ano_anterior > 0:
                crecimiento = ((total_ano - total_ano_anterior) / total_ano_anterior) * 100
            
            return jsonify({
                'success': True,
                'ano': ano,
                'datos_mensuales': datos_mensuales,
                'resumen': {
                    'total_ventas_ano': total_ventas_ano,
                    'total_dinero_ano': round(total_ano, 2),
                    'promedio_mensual': round(promedio_mensual, 2),
                    'mes_mayor': {
                        'mes': mes_mayor['nombre_mes'],
                        'total': mes_mayor['total_ventas']
                    },
                    'mes_menor': {
                        'mes': mes_menor['nombre_mes'],
                        'total': mes_menor['total_ventas']
                    },
                    'crecimiento_anual': round(crecimiento, 1),
                    'total_ano_anterior': round(total_ano_anterior, 2)
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @estadisticas_bp.route('/api/comparacion_anos')
    def comparacion_anos():
        try:
            anos = request.args.getlist('anos', type=int)
            if not anos:
                # Por defecto: año actual y anterior
                ano_actual = datetime.now().year
                anos = [ano_actual - 1, ano_actual]
            
            datos_comparacion = []
            
            for ano in anos:
                ventas_ano = db.session.query(
                    extract('month', Factura.fecha).label('mes'),
                    func.sum(Factura.total).label('total')
                ).filter(
                    extract('year', Factura.fecha) == ano,
                    Factura.estado != 'cancelada'
                ).group_by(
                    extract('month', Factura.fecha)
                ).all()
                
                # Crear array con todos los meses
                ventas_mensuales = [0] * 12
                for venta in ventas_ano:
                    ventas_mensuales[venta.mes - 1] = float(venta.total)
                
                datos_comparacion.append({
                    'ano': ano,
                    'ventas_mensuales': ventas_mensuales,
                    'total_ano': sum(ventas_mensuales)
                })
            
            return jsonify({
                'success': True,
                'datos': datos_comparacion,
                'meses': [calendar.month_abbr[i] for i in range(1, 13)]
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @estadisticas_bp.route('/api/top_productos_mes')
    def top_productos_mes():
        try:
            mes = request.args.get('mes', type=int)
            ano = request.args.get('ano', type=int)
            limite = request.args.get('limite', 10, type=int)
            
            nombres_meses = [
                '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ]
            
            # Consulta usando SQLAlchemy en lugar de SQL crudo
            top_productos = db.session.query(
                Producto.codigo,
                Producto.nombre,
                func.sum(DetalleFactura.cantidad).label('cantidad_vendida'),
                func.sum(DetalleFactura.cantidad * DetalleFactura.precio_unitario).label('total_vendido')
            ).join(
                DetalleFactura, Producto.id == DetalleFactura.producto_id
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                extract('month', Factura.fecha) == mes,
                extract('year', Factura.fecha) == ano,
                Factura.estado == 'autorizada'
            ).group_by(
                Producto.id, Producto.codigo, Producto.nombre
            ).order_by(
                func.sum(DetalleFactura.cantidad).desc()
            ).limit(limite).all()
            
            productos = []
            for producto in top_productos:
                productos.append({
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'cantidad_vendida': int(producto.cantidad_vendida),
                    'total_vendido': float(producto.total_vendido)
                })
            
            return jsonify({
                'success': True,
                'productos': productos,
                'nombre_mes': nombres_meses[mes] if 1 <= mes <= 12 else f'Mes {mes}'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @estadisticas_bp.route('/api/ventas_diarias')
    def ventas_diarias():
        """Estadísticas de ventas por día (últimos 30 días)"""
        try:
            dias = request.args.get('dias', 30, type=int)
            fecha_inicio = datetime.now() - timedelta(days=dias-1)
            
            ventas_diarias = db.session.query(
                func.date(Factura.fecha).label('fecha'),
                func.count(Factura.id).label('cantidad_ventas'),
                func.sum(Factura.total).label('total_ventas')
            ).filter(
                Factura.fecha >= fecha_inicio,
                Factura.estado != 'cancelada'
            ).group_by(
                func.date(Factura.fecha)
            ).order_by('fecha').all()
            
            # Crear estructura completa de días
            datos_diarios = []
            ventas_dict = {str(v.fecha): v for v in ventas_diarias}
            
            for i in range(dias):
                fecha = (fecha_inicio + timedelta(days=i)).date()
                fecha_str = str(fecha)
                venta_dia = ventas_dict.get(fecha_str)
                
                datos_diarios.append({
                    'fecha': fecha_str,
                    'fecha_formateada': fecha.strftime('%d/%m'),
                    'dia_semana': fecha.strftime('%A'),
                    'cantidad_ventas': int(venta_dia.cantidad_ventas) if venta_dia else 0,
                    'total_ventas': float(venta_dia.total_ventas) if venta_dia else 0.0
                })
            
            return jsonify({
                'success': True,
                'datos_diarios': datos_diarios,
                'periodo': f'Últimos {dias} días'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @estadisticas_bp.route('/api/resumen_dashboard')
    def resumen_dashboard():
        """Resumen general para el dashboard"""
        try:
            # Ventas de hoy
            hoy = datetime.now().date()
            ventas_hoy = db.session.query(
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.total).label('total')
            ).filter(
                func.date(Factura.fecha) == hoy,
                Factura.estado != 'cancelada'
            ).first()
            
            # Ventas del mes actual
            mes_actual = datetime.now().month
            ano_actual = datetime.now().year
            ventas_mes = db.session.query(
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.total).label('total')
            ).filter(
                extract('month', Factura.fecha) == mes_actual,
                extract('year', Factura.fecha) == ano_actual,
                Factura.estado != 'cancelada'
            ).first()
            
            # Top 5 productos del mes
            top_productos = db.session.query(
                Producto.nombre,
                func.sum(DetalleFactura.cantidad).label('cantidad_vendida')
            ).join(
                DetalleFactura, Producto.id == DetalleFactura.producto_id
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                extract('month', Factura.fecha) == mes_actual,
                extract('year', Factura.fecha) == ano_actual,
                Factura.estado != 'cancelada'
            ).group_by(
                Producto.id, Producto.nombre
            ).order_by(
                func.sum(DetalleFactura.cantidad).desc()
            ).limit(5).all()
            
            return jsonify({
                'success': True,
                'ventas_hoy': {
                    'cantidad': int(ventas_hoy.cantidad) if ventas_hoy.cantidad else 0,
                    'total': float(ventas_hoy.total) if ventas_hoy.total else 0.0
                },
                'ventas_mes': {
                    'cantidad': int(ventas_mes.cantidad) if ventas_mes.cantidad else 0,
                    'total': float(ventas_mes.total) if ventas_mes.total else 0.0
                },
                'top_productos': [
                    {
                        'nombre': p.nombre,
                        'cantidad': float(p.cantidad_vendida)
                    } for p in top_productos
                ]
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return estadisticas_bp