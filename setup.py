from setuptools import setup

setup(
    name="scalinator",
    version="0.0.4",
    python_requires='~=3.6',
    description="Demonstrating TPS based pod autoscaling within OpenShift",
    author="Julian Gericke, LSD Information Technology",
    author_email="julian@lsd.co.za",
    license='WTFPL',
    scripts=["bin/scaler.py"],
    install_requires=[
        'requests==2.20.0',
        'haproxystats==0.3.15',
        'urllib3==1.24.2',
        'APScheduler==3.4.0',
        'biome==0.1.3'
    ],
    extras_require={
        'dev': [
            "coverage==4.4.2",
            "flake8==3.5.0",
            "pytest==3.2.3",
            "pytest-env==0.6.2"
         ]
    }
)
