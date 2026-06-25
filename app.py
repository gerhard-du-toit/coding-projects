from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, IPAddress, NumberRange
import ipaddress
import statistics
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
    ping_count = IntegerField(
        'Ping Count',
        default=4,
        validators=[
            DataRequired(message='Ping count is required'),
            NumberRange(min=1, max=20, message='Ping count must be between 1 and 20')
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
        ping_count = form.ping_count.data
        try:
            # Validate IP address
            ipaddress.ip_address(ip)
            monitor = PingMonitor(host=ip, window_size=ping_count, interval=0.5)
            ping_results = monitor.ping_batch(ping_count)
            successful = [r for r in ping_results if r.get('success')]
            latencies = [r.get('latency') for r in successful if r.get('latency') is not None]

            ping_data = {
                'host': ip,
                'count': ping_count,
                'results': ping_results,
                'success_count': len(successful),
                'loss_count': ping_count - len(successful),
                'min_latency': min(latencies) if latencies else None,
                'max_latency': max(latencies) if latencies else None,
                'avg_latency': statistics.mean(latencies) if latencies else None,
                'max_display_latency': max(latencies) if latencies else 100
            }

            if ping_data['success_count'] > 0:
                result = (
                    f"Pinged {ip} {ping_count} times: "
                    f"{ping_data['success_count']} success, {ping_data['loss_count']} loss, "
                    f"avg {ping_data['avg_latency']:.2f} ms"
                )
            else:
                error = f"All pings to {ip} failed."
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