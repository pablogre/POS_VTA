<!-- templates/factura_detalle.html -->
{% extends "base.html" %}

{% block title %}Factura {{ factura.numero }} - POS Argentina{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">Factura {{ factura.numero }}</h1>
    <div>
        <button class="btn btn-secondary" onclick="window.print()">
            <i class="fas fa-print"></i> Imprimir
        </button>
        <a href="{{ url_for('facturas') }}" class="btn btn-primary">
            <i class="fas fa-arrow-left"></i> Volver
        </a>
    </div>
</div>

<div class="card">
    <div class="card-body" id="factura-content">
        <!-- Encabezado de la factura -->
        <div class="row mb-4">
            <div class="col-md-6">
                <h4>MI EMPRESA SRL</h4>
                <p class="mb-1">CUIT: 20-12345678-9</p>
                <p class="mb-1">Av. Corrientes 1234, CABA</p>
                <p class="mb-1">Tel: 011-1234-5678</p>
                <p class="mb-1">info@miempresa.com</p>
            </div>
            <div class="col-md-6 text-end">
                <div class="border p-3 bg-light">
                    <h5>
                        {% if factura.tipo_comprobante == '01' %}FACTURA A
                        {% elif factura.tipo_comprobante == '06' %}FACTURA B
                        {% elif factura.tipo_comprobante == '11' %}FACTURA C
                        {% else %}COMPROBANTE
                        {% endif %}
                    </h5>
                    <p class="mb-1"><strong>Nº:</strong> {{ factura.numero }}</p>
                    <p class="mb-1"><strong>Fecha:</strong> {{ factura.fecha.strftime('%d/%m/%Y') }}</p>
                    {% if factura.cae %}
                    <p class="mb-1"><strong>CAE:</strong> {{ factura.cae }}</p>
                    <p class="mb-1"><strong>Vto CAE:</strong> {{ factura.vto_cae.strftime('%d/%m/%Y') if factura.vto_cae else '-' }}</p>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Datos del cliente -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="border p-3 bg-light">
                    <h6><strong>DATOS DEL CLIENTE:</strong></h6>
                    <div class="row">
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Nombre:</strong> {{ factura.cliente.nombre }}</p>
                            <p class="mb-1"><strong>Documento:</strong> {{ factura.cliente.tipo_documento }}: {{ factura.cliente.documento }}</p>
                        </div>
                        <div class="col-md-6">
                            {% if factura.cliente.direccion %}
                            <p class="mb-1"><strong>Dirección:</strong> {{ factura.cliente.direccion }}</p>
                            {% endif %}
                            <p class="mb-1"><strong>Condición IVA:</strong> {{ factura.cliente.condicion_iva.replace('_', ' ').title() }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Detalle de productos -->
        <div class="table-responsive mb-4">
            <table class="table table-bordered">
                <thead class="table-dark">
                    <tr>
                        <th>Código</th>
                        <th>Descripción</th>
                        <th class="text-center">Cantidad</th>
                        <th class="text-end">Precio Unit.</th>
                        <th class="text-end">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {% for detalle in factura.detalles %}
                    <tr>
                        <td><code>{{ detalle.producto.codigo }}</code></td>
                        <td>{{ detalle.producto.nombre }}</td>
                        <td class="text-center">{{ detalle.cantidad }}</td>
                        <td class="text-end">${{ "%.2f"|format(detalle.precio_unitario) }}</td>
                        <td class="text-end">${{ "%.2f"|format(detalle.subtotal) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Totales -->
        <div class="row justify-content-end">
            <div class="col-md-4">
                <table class="table table-sm">
                    <tr>
                        <td><strong>Subtotal:</strong></td>
                        <td class="text-end">${{ "%.2f"|format(factura.subtotal) }}</td>
                    </tr>
                    <tr>
                        <td><strong>IVA:</strong></td>
                        <td class="text-end">${{ "%.2f"|format(factura.iva) }}</td>
                    </tr>
                    <tr class="table-primary">
                        <td><strong>TOTAL:</strong></td>
                        <td class="text-end"><strong>${{ "%.2f"|format(factura.total) }}</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Estado de la factura -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="border p-3 bg-light">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Estado:</strong> 
                                {% if factura.estado == 'autorizada' %}
                                    <span class="badge bg-success">Autorizada por AFIP</span>
                                {% elif factura.estado == 'error_afip' %}
                                    <span class="badge bg-warning">Error de conexión con AFIP</span>
                                {% else %}
                                    <span class="badge bg-secondary">{{ factura.estado.title() }}</span>
                                {% endif %}
                            </p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Procesado por:</strong> {{ factura.usuario.nombre }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
@media print {
    .btn, .border-bottom, .pt-3, .pb-2, .mb-3, nav, .sidebar {
        display: none !important;
    }
    .card {
        border: none !important;
        box-shadow: none !important;
    }
    .content {
        margin-left: 0 !important;
    }
    body {
        font-size: 12px;
    }
}
</style>
{% endblock %}