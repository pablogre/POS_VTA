# caja.py - Sistema de Caja SIMPLIFICADO para evitar problemas de relaciones

#### ver estas rutas para debug
#http://localhost:5080/api/caja/estado muestra el estado de la caja
#http://localhost:5080/api/caja/ultima muestra como esta conformada la caja


from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, desc, asc, text
from decimal import Decimal

# Variables globales para los modelos
CajaAperturaModel = None
MovimientoCajaModel = None

# ==================== MODELOS SIMPLIFICADOS ====================

def init_caja_models(db):
    """Inicializar modelos de caja SIMPLIFICADOS"""
    global CajaAperturaModel, MovimientoCajaModel
    
    class CajaAperturaModel(db.Model):
        __tablename__ = 'cajas'
        
        id = db.Column(db.Integer, primary_key=True)
        fecha_apertura = db.Column(db.DateTime, nullable=False, default=datetime.now)
        fecha_cierre = db.Column(db.DateTime, nullable=True)
        monto_inicial = db.Column(db.Numeric(10, 2), nullable=False)
        monto_cierre = db.Column(db.Numeric(10, 2), nullable=True)
        efectivo_teorico = db.Column(db.Numeric(10, 2), nullable=True)
        efectivo_real = db.Column(db.Numeric(10, 2), nullable=True)
        diferencia = db.Column(db.Numeric(10, 2), nullable=True)
        observaciones_apertura = db.Column(db.Text)
        observaciones_cierre = db.Column(db.Text)
        usuario_apertura_id = db.Column(db.Integer, nullable=False, default=3)
        usuario_cierre_id = db.Column(db.Integer, nullable=True)
        estado = db.Column(db.String(20), default='abierta')
        activa = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.TIMESTAMP, default=datetime.now)
        
        # MÉTODO PARA CALCULAR EFECTIVO TEÓRICO AUTOMÁTICAMENTE
        def calcular_efectivo_teorico(self, db):
            """Calcular efectivo teórico basado en movimientos reales"""
            try:
                # Obtener todos los movimientos de esta caja
                movimientos = MovimientoCajaModel.query.filter_by(caja_id=self.id).all()
                
                # Empezar con el monto inicial
                efectivo_teorico = float(self.monto_inicial)
                
                # Sumar ingresos y restar egresos de movimientos manuales
                for mov in movimientos:
                    if mov.tipo == 'ingreso':
                        efectivo_teorico += float(mov.monto)
                    elif mov.tipo == 'egreso':
                        efectivo_teorico -= float(mov.monto)
                
                # CALCULAR VENTAS EN EFECTIVO DE ESTA CAJA
                # Buscar facturas que pertenezcan al rango de fechas de esta caja
                fecha_inicio = self.fecha_apertura
                fecha_fin = self.fecha_cierre if self.fecha_cierre else datetime.now()
                
                # Query para obtener ventas en efectivo - CORREGIDA
                ventas_efectivo_query = """
                    SELECT COALESCE(SUM(mp.importe), 0) as total_efectivo
                    FROM medios_pago mp
                    INNER JOIN factura f ON mp.factura_id = f.id
                    WHERE mp.medio_pago = 'efectivo' 
                    AND f.estado != 'anulada'
                    AND f.fecha BETWEEN :fecha_inicio AND :fecha_fin
                """
                
                result = db.session.execute(text(ventas_efectivo_query), {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                })
                ventas_efectivo = float(result.fetchone()[0] or 0)
                efectivo_teorico += ventas_efectivo
                
                # RESTAR GASTOS EN EFECTIVO DE ESTA CAJA - CORREGIDA
                gastos_efectivo_query = """
                    SELECT COALESCE(SUM(monto), 0) as total_gastos
                    FROM gastos
                    WHERE metodo_pago = 'efectivo'
                    AND activo = 1
                    AND fecha BETWEEN DATE(:fecha_inicio) AND DATE(:fecha_fin)
                """
                
                result = db.session.execute(text(gastos_efectivo_query), {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                })
                gastos_efectivo = float(result.fetchone()[0] or 0)
                efectivo_teorico -= gastos_efectivo
                
                print(f"🧮 Cálculo efectivo teórico Caja {self.id}:")
                print(f"   - Monto inicial: ${float(self.monto_inicial)}")
                print(f"   - Movimientos manuales: +${sum(float(m.monto) for m in movimientos if m.tipo == 'ingreso')} / -${sum(float(m.monto) for m in movimientos if m.tipo == 'egreso')}")
                print(f"   - Ventas en efectivo: +${ventas_efectivo}")
                print(f"   - Gastos en efectivo: -${gastos_efectivo}")
                print(f"   - TOTAL EFECTIVO TEÓRICO: ${efectivo_teorico}")
                
                return efectivo_teorico
                
            except Exception as e:
                print(f"Error calculando efectivo teórico: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return float(self.monto_inicial)
        
        def to_dict(self, db=None):
            # Si se proporciona db, calcular efectivo teórico en tiempo real
            efectivo_teorico_calculado = self.efectivo_teorico
            if db and self.estado == 'abierta':
                efectivo_teorico_calculado = self.calcular_efectivo_teorico(db)
            
            return {
                'id': self.id,
                'fecha_apertura': self.fecha_apertura.isoformat() if self.fecha_apertura else None,
                'fecha_cierre': self.fecha_cierre.isoformat() if self.fecha_cierre else None,
                'monto_inicial': float(self.monto_inicial) if self.monto_inicial else 0.0,
                'monto_cierre': float(self.monto_cierre) if self.monto_cierre else 0.0,
                'efectivo_teorico': float(efectivo_teorico_calculado) if efectivo_teorico_calculado else 0.0,
                'efectivo_real': float(self.efectivo_real) if self.efectivo_real else 0.0,
                'diferencia': float(self.diferencia) if self.diferencia else 0.0,
                'observaciones_apertura': self.observaciones_apertura,
                'observaciones_cierre': self.observaciones_cierre,
                'estado': self.estado,
                'activa': self.activa,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

    class MovimientoCajaModel(db.Model):
        __tablename__ = 'movimientos_caja'
        
        id = db.Column(db.Integer, primary_key=True)
        caja_id = db.Column(db.Integer, nullable=False)
        tipo = db.Column(db.String(10), nullable=False)
        descripcion = db.Column(db.String(255), nullable=False)
        monto = db.Column(db.Numeric(10, 2), nullable=False)
        notas = db.Column(db.Text)
        fecha = db.Column(db.DateTime, default=datetime.now, nullable=False)
        usuario_id = db.Column(db.Integer, nullable=False, default=3)
        created_at = db.Column(db.TIMESTAMP, default=datetime.now)
        
        def to_dict(self):
            return {
                'id': self.id,
                'caja_id': self.caja_id,
                'tipo': self.tipo,
                'descripcion': self.descripcion,
                'monto': float(self.monto),
                'notas': self.notas,
                'fecha': self.fecha.isoformat() if self.fecha else None,
                'usuario_id': self.usuario_id,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

    return CajaAperturaModel, MovimientoCajaModel

# ==================== RUTAS DE API ====================

def init_caja_routes(caja_bp, db):
    """Inicializar rutas de caja en el blueprint"""
    global CajaAperturaModel, MovimientoCajaModel

    @caja_bp.route('/api/caja/estado')
    def obtener_estado_caja():
        """Obtener estado actual de la caja"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Usuario por defecto para pruebas
            # return jsonify({'error': 'No autorizado'}), 401
        
        try:
            caja_abierta = CajaAperturaModel.query.filter_by(
                estado='abierta',
                activa=True
            ).order_by(CajaAperturaModel.id.desc()).first()
            
            if caja_abierta:
                return jsonify({
                    'success': True,
                    'caja_abierta': True,
                    'caja': caja_abierta.to_dict(db)  # Pasar db para cálculo en tiempo real
                })
            else:
                return jsonify({
                    'success': True,
                    'caja_abierta': False,
                    'caja': None
                })
                
        except Exception as e:
            print(f"Error obteniendo estado de caja: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @caja_bp.route('/api/caja/ultima')
    def obtener_ultima_caja():
        """Obtener la última caja (abierta o cerrada más reciente)"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Temporal para pruebas
        
        try:
            ultima_caja = CajaAperturaModel.query.filter_by(
                activa=True
            ).order_by(CajaAperturaModel.id.desc()).first()
            
            if ultima_caja:
                return jsonify({
                    'success': True,
                    'caja': ultima_caja.to_dict(db)
                })
            else:
                return jsonify({
                    'success': False,
                    'caja': None,
                    'message': 'No hay cajas registradas'
                })
                
        except Exception as e:
            print(f"Error obteniendo última caja: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @caja_bp.route('/api/caja/abrir', methods=['POST'])
    def abrir_caja():
        """Abrir nueva caja"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Temporal para pruebas
            # return jsonify({'error': 'No autorizado'}), 401
        
        try:
            data = request.get_json()
            
            # Validar que no haya una caja abierta
            caja_existente = CajaAperturaModel.query.filter_by(
                estado='abierta',
                activa=True
            ).first()
            
            if caja_existente:
                return jsonify({
                    'success': False,
                    'error': 'Ya hay una caja abierta. Debe cerrarla primero.'
                }), 400
            
            # Validar datos
            monto_inicial = float(data.get('monto_inicial', 0))
            if monto_inicial < 0:
                return jsonify({
                    'success': False,
                    'error': 'El monto inicial no puede ser negativo'
                }), 400
            
            # Crear nueva apertura
            nueva_caja = CajaAperturaModel(
                monto_inicial=Decimal(str(monto_inicial)),
                observaciones_apertura=data.get('observaciones', ''),
                usuario_apertura_id=session['user_id'],
                fecha_apertura=datetime.now(),
                efectivo_teorico=Decimal(str(monto_inicial))  # Inicializar con monto inicial
            )
            
            db.session.add(nueva_caja)
            db.session.commit()
            
            print(f"Caja abierta: ID {nueva_caja.id}, Monto inicial: ${monto_inicial}")
            
            return jsonify({
                'success': True,
                'message': 'Caja abierta exitosamente',
                'caja': nueva_caja.to_dict(db)
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Error abriendo caja: {e}")
            return jsonify({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }), 500

    @caja_bp.route('/api/caja/cerrar', methods=['POST'])
    def cerrar_caja():
        """Cerrar caja actual"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Temporal para pruebas
            # return jsonify({'error': 'No autorizado'}), 401
        
        try:
            data = request.get_json()
            caja_id = data.get('caja_id')
            
            # Buscar caja abierta
            caja = CajaAperturaModel.query.filter_by(
                id=caja_id,
                estado='abierta',
                activa=True
            ).first()
            
            if not caja:
                return jsonify({
                    'success': False,
                    'error': 'No se encontró caja abierta'
                }), 404
            
            # Calcular efectivo teórico automáticamente
            efectivo_teorico = caja.calcular_efectivo_teorico(db)
            
            # Validar datos de cierre
            efectivo_real = float(data.get('efectivo_real', 0))
            
            if efectivo_real < 0:
                return jsonify({
                    'success': False,
                    'error': 'El efectivo real no puede ser negativo'
                }), 400
            
            # Calcular diferencia
            diferencia = efectivo_real - efectivo_teorico
            
            # Actualizar caja
            caja.fecha_cierre = datetime.now()
            caja.efectivo_teorico = Decimal(str(efectivo_teorico))
            caja.efectivo_real = Decimal(str(efectivo_real))
            caja.diferencia = Decimal(str(diferencia))
            caja.observaciones_cierre = data.get('observaciones', '')
            caja.usuario_cierre_id = session['user_id']
            caja.estado = 'cerrada'
            
            db.session.commit()
            
            print(f"Caja cerrada: ID {caja.id}, Diferencia: ${diferencia}")
            
            return jsonify({
                'success': True,
                'message': 'Caja cerrada exitosamente',
                'caja': caja.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Error cerrando caja: {e}")
            return jsonify({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }), 500

    @caja_bp.route('/api/caja/movimiento', methods=['POST'])
    def registrar_movimiento():
        """Registrar movimiento adicional en caja"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Temporal para pruebas
            # return jsonify({'error': 'No autorizado'}), 401
        
        try:
            data = request.get_json()
            
            # Validar datos
            caja_id = data.get('caja_id')
            tipo = data.get('tipo')  # ingreso o egreso
            descripcion = data.get('descripcion', '').strip()
            monto = float(data.get('monto', 0))
            
            print(f"Intentando registrar movimiento: caja_id={caja_id}, tipo={tipo}, monto={monto}")
            
            if not caja_id or not tipo or not descripcion or monto <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Datos incompletos o inválidos'
                }), 400
            
            if tipo not in ['ingreso', 'egreso']:
                return jsonify({
                    'success': False,
                    'error': 'Tipo de movimiento inválido'
                }), 400
            
            # Verificar que la caja existe y está abierta
            caja = CajaAperturaModel.query.filter_by(
                id=caja_id,
                estado='abierta',
                activa=True
            ).first()
            
            if not caja:
                return jsonify({
                    'success': False,
                    'error': 'Caja no encontrada o cerrada'
                }), 404
            
            # Crear movimiento
            movimiento = MovimientoCajaModel(
                caja_id=caja_id,
                tipo=tipo,
                descripcion=descripcion,
                monto=Decimal(str(monto)),
                notas=data.get('notas', ''),
                usuario_id=session['user_id'],
                fecha=datetime.now()
            )
            
            db.session.add(movimiento)
            
            # ACTUALIZAR EFECTIVO TEÓRICO AUTOMÁTICAMENTE
            efectivo_teorico_actual = caja.calcular_efectivo_teorico(db)
            if tipo == 'ingreso':
                nuevo_efectivo_teorico = efectivo_teorico_actual + monto
            else:  # egreso
                nuevo_efectivo_teorico = efectivo_teorico_actual - monto
            
            caja.efectivo_teorico = Decimal(str(nuevo_efectivo_teorico))
            
            db.session.commit()
            
            print(f"Movimiento registrado exitosamente: ID {movimiento.id}")
            print(f"Efectivo teórico actualizado a: ${nuevo_efectivo_teorico}")
            
            return jsonify({
                'success': True,
                'message': f'{tipo.title()} registrado exitosamente',
                'movimiento': movimiento.to_dict(),
                'efectivo_teorico_actualizado': nuevo_efectivo_teorico
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Error registrando movimiento: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }), 500

    @caja_bp.route('/api/caja/<int:caja_id>/movimientos')
    def obtener_movimientos_caja(caja_id):
        """Obtener movimientos de una caja específica"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Temporal para pruebas
            # return jsonify({'error': 'No autorizado'}), 401
        
        try:
            movimientos = MovimientoCajaModel.query.filter_by(
                caja_id=caja_id
            ).order_by(MovimientoCajaModel.fecha.desc()).all()
            
            movimientos_data = [mov.to_dict() for mov in movimientos]
            
            return jsonify({
                'success': True,
                'movimientos': movimientos_data
            })
            
        except Exception as e:
            print(f"Error obteniendo movimientos: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @caja_bp.route('/api/caja/<int:caja_id>/resumen')
    def obtener_resumen_caja(caja_id):
        """Obtener resumen completo de una caja con cálculos correctos"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Temporal para pruebas
            # return jsonify({'error': 'No autorizado'}), 401
        
        try:
            caja = CajaAperturaModel.query.get(caja_id)
            if not caja:
                return jsonify({
                    'success': False,
                    'error': 'Caja no encontrada'
                }), 404
            
            # Obtener movimientos manuales
            movimientos = MovimientoCajaModel.query.filter_by(
                caja_id=caja_id
            ).order_by(MovimientoCajaModel.fecha.desc()).all()
            
            # Calcular totales de movimientos manuales
            total_ingresos_manuales = sum(float(mov.monto) for mov in movimientos if mov.tipo == 'ingreso')
            total_egresos_manuales = sum(float(mov.monto) for mov in movimientos if mov.tipo == 'egreso')
            
            # Efectivo teórico calculado automáticamente (incluye ventas y gastos)
            efectivo_teorico = caja.calcular_efectivo_teorico(db)
            
            # Obtener detalles de ventas y gastos para el reporte
            fecha_inicio = caja.fecha_apertura
            fecha_fin = caja.fecha_cierre if caja.fecha_cierre else datetime.now()
            
            # Ventas en efectivo - CORREGIDA
            ventas_efectivo_query = """
                SELECT COALESCE(SUM(mp.importe), 0) as total_efectivo,
                       COUNT(DISTINCT f.id) as cantidad_ventas
                FROM medios_pago mp
                INNER JOIN factura f ON mp.factura_id = f.id
                WHERE mp.medio_pago = 'efectivo' 
                AND f.estado != 'anulada'
                AND f.fecha BETWEEN :fecha_inicio AND :fecha_fin
            """
            result = db.session.execute(text(ventas_efectivo_query), {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            })
            venta_data = result.fetchone()
            total_ventas_efectivo = float(venta_data[0] or 0)
            cantidad_ventas = int(venta_data[1] or 0)
            
            # Gastos en efectivo - CORREGIDA
            gastos_efectivo_query = """
                SELECT COALESCE(SUM(monto), 0) as total_gastos,
                       COUNT(*) as cantidad_gastos
                FROM gastos
                WHERE metodo_pago = 'efectivo'
                AND activo = 1
                AND fecha BETWEEN DATE(:fecha_inicio) AND DATE(:fecha_fin)
            """
            result = db.session.execute(text(gastos_efectivo_query), {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            })
            gasto_data = result.fetchone()
            total_gastos_efectivo = float(gasto_data[0] or 0)
            cantidad_gastos = int(gasto_data[1] or 0)
            
            resumen = {
                'caja': caja.to_dict(db),
                'movimientos': [mov.to_dict() for mov in movimientos],
                'totales': {
                    'monto_inicial': float(caja.monto_inicial),
                    'movimientos_manuales': {
                        'total_ingresos': total_ingresos_manuales,
                        'total_egresos': total_egresos_manuales,
                        'balance_neto': total_ingresos_manuales - total_egresos_manuales,
                        'cantidad_movimientos': len(movimientos)
                    },
                    'ventas_sistema': {
                        'total_efectivo': total_ventas_efectivo,
                        'cantidad_ventas': cantidad_ventas
                    },
                    'gastos_sistema': {
                        'total_efectivo': total_gastos_efectivo,
                        'cantidad_gastos': cantidad_gastos
                    },
                    'efectivo_teorico': efectivo_teorico,
                    'calculo_detallado': {
                        'apertura': float(caja.monto_inicial),
                        'ingresos_manuales': total_ingresos_manuales,
                        'ventas_efectivo': total_ventas_efectivo,
                        'egresos_manuales': -total_egresos_manuales,
                        'gastos_efectivo': -total_gastos_efectivo,
                        'total': efectivo_teorico
                    }
                }
            }
            
            return jsonify({
                'success': True,
                'resumen': resumen
            })
            
        except Exception as e:
            print(f"Error obteniendo resumen de caja: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @caja_bp.route('/api/caja/<int:caja_id>/ventas')
    def obtener_ventas_caja(caja_id):
        """Obtener detalle de ventas en efectivo de una caja"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Temporal para pruebas
            # return jsonify({'error': 'No autorizado'}), 401
        
        try:
            caja = CajaAperturaModel.query.get(caja_id)
            if not caja:
                return jsonify({'success': False, 'error': 'Caja no encontrada'}), 404
            
            fecha_inicio = caja.fecha_apertura
            fecha_fin = caja.fecha_cierre if caja.fecha_cierre else datetime.now()
            
            # Query para obtener ventas detalladas - CORREGIDA
            ventas_query = """
                SELECT f.id, f.numero, f.fecha, f.total, mp.importe as efectivo,
                       c.nombre as cliente
                FROM factura f
                INNER JOIN medios_pago mp ON f.id = mp.factura_id
                LEFT JOIN cliente c ON f.cliente_id = c.id
                WHERE mp.medio_pago = 'efectivo' 
                AND f.estado != 'anulada'
                AND f.fecha BETWEEN :fecha_inicio AND :fecha_fin
                ORDER BY f.fecha DESC
            """
            
            result = db.session.execute(text(ventas_query), {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            })
            ventas = []
            
            for row in result.fetchall():
                ventas.append({
                    'factura_id': row[0],
                    'numero': row[1],
                    'fecha': row[2].isoformat() if row[2] else None,
                    'total_factura': float(row[3]),
                    'efectivo_cobrado': float(row[4]),
                    'cliente': row[5] or 'Cliente Final'
                })
            
            return jsonify({
                'success': True,
                'ventas': ventas,
                'total_efectivo': sum(v['efectivo_cobrado'] for v in ventas),
                'cantidad_ventas': len(ventas)
            })
            
        except Exception as e:
            print(f"Error obteniendo ventas de caja: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @caja_bp.route('/api/caja/<int:caja_id>/gastos')
    def obtener_gastos_caja(caja_id):
        """Obtener detalle de gastos en efectivo de una caja"""
        if 'user_id' not in session:
            session['user_id'] = 3  # Temporal para pruebas
            # return jsonify({'error': 'No autorizado'}), 401
        
        try:
            caja = CajaAperturaModel.query.get(caja_id)
            if not caja:
                return jsonify({'success': False, 'error': 'Caja no encontrada'}), 404
            
            fecha_inicio = caja.fecha_apertura
            fecha_fin = caja.fecha_cierre if caja.fecha_cierre else datetime.now()
            
            # Query para obtener gastos detallados - CORREGIDA
            gastos_query = """
                SELECT id, fecha, descripcion, monto, categoria, notas
                FROM gastos
                WHERE metodo_pago = 'efectivo'
                AND activo = 1
                AND fecha BETWEEN DATE(:fecha_inicio) AND DATE(:fecha_fin)
                ORDER BY fecha DESC
            """
            
            result = db.session.execute(text(gastos_query), {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            })
            gastos = []
            
            for row in result.fetchall():
                gastos.append({
                    'id': row[0],
                    'fecha': row[1].isoformat() if row[1] else None,
                    'descripcion': row[2],
                    'monto': float(row[3]),
                    'categoria': row[4],
                    'notas': row[5] or ''
                })
            
            return jsonify({
                'success': True,
                'gastos': gastos,
                'total_gastos': sum(g['monto'] for g in gastos),
                'cantidad_gastos': len(gastos)
            })
            
        except Exception as e:
            print(f"Error obteniendo gastos de caja: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

# ==================== FUNCIÓN DE INICIALIZACIÓN ====================

def init_caja_system(db, Factura, DetalleFactura, Producto, Usuario, MedioPago, Gasto):
    """Inicializar sistema de caja SIMPLIFICADO"""
    
    # Inicializar modelos
    global CajaAperturaModel, MovimientoCajaModel
    CajaAperturaModel, MovimientoCajaModel = init_caja_models(db)
    
    # Crear blueprint
    caja_bp = Blueprint('caja', __name__)
    
    # Registrar rutas en el blueprint
    init_caja_routes(caja_bp, db)
    
    print("✅ Sistema de caja SIMPLIFICADO inicializado correctamente")
    
    return caja_bp

# ==================== FUNCIONES AUXILIARES ====================

def crear_tablas_caja(db):
    """Las tablas ya existen - no hacer nada"""
    print("✅ Tablas de caja ya existen")

def migrar_datos_caja():
    """No hay migración necesaria"""
    print("✅ No hay migración necesaria")