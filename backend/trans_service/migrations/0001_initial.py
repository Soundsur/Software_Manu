
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # Dependemos del user model que vive en auth_service
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('confirmado_en', models.DateTimeField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('CONFIRMADA', 'Confirmada'), ('FALLIDA', 'Fallida')], default='PENDIENTE', max_length=10)),
                ('descuento_carrito', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('porcentaje_descuento', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transacciones', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'transaccion',
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('producto_codigo', models.CharField(blank=True, max_length=100, null=True)),
                ('producto_nombre', models.CharField(blank=True, max_length=300, null=True)),
                ('producto_precio', models.IntegerField(blank=True, null=True)),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('eliminado', models.BooleanField(default=False)),
                ('transaccion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trans_service.transaccion')),
            ],
            options={
                'db_table': 'item',
            },
        ),
    ]
