from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, IPAddress
import ipaddress
from monitor.ping_monitor import PingMonitor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'


class IPAddressForm(FlaskForm):
    """Form to accept and validate IP addresses"""
    ip_address = StringField(
        'IP Address',
        validators=[
            DataRequired(message='IP address is required'),
            IPAddress(message='Invalid IP address format')
        ]
    )
    submit = SubmitField('Ping')


@app.route("/", methods=['GET', 'POST'])
def home():
    form = IPAddressForm()
    result = None
    error = None
    ping_data = None
    
    if form.validate_on_submit():
        ip = form.ip_address.data
        try:
            # Validate IP address
            ipaddress.ip_address(ip)
            monitor = PingMonitor(host=ip)
            ping_data = monitor.ping_once()

            if ping_data.get('success'):
                result = f"Ping successful to {ip}: {ping_data.get('latency'):.2f} ms"
            else:
                error = f"Ping failed for {ip}."
        except ValueError:
            error = "Invalid IP address"
    
    return render_template(
        'index.html',
        form=form,
        result=result,
        error=error,
        ping_data=ping_data
    )


@app.route("/api/ping", methods=['POST'])
def api_ping():
    """API endpoint to handle IP address submission"""
    data = request.get_json()
    ip = data.get('ip_address', '').strip()
    
    if not ip:
        return jsonify({'error': 'IP address is required'}), 400
    
    try:
        ipaddress.ip_address(ip)
        ping_data = PingMonitor(host=ip).ping_once()
        return jsonify({
            'success': ping_data.get('success', False),
            'latency': ping_data.get('latency'),
            'ip': ip
        }), 200
    except ValueError:
        return jsonify({'error': 'Invalid IP address format'}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)