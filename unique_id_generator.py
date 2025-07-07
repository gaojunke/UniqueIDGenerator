from qgis.PyQt.QtWidgets import QAction, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QListWidget, QSpinBox, QHBoxLayout, QListWidgetItem, QComboBox
from qgis.core import QgsProject, QgsVectorLayer, QgsField
from PyQt5.QtCore import QVariant, QCoreApplication
import os

class UniqueIDGenerator:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dlg = None

    def initGui(self):
        self.action = QAction("UniqueIDGenerator", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("UniqueIDGenerator", self.action)

    def unload(self):
        self.iface.removePluginMenu("UniqueIDGenerator", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        self.dlg = QDialog()
        self.dlg.setWindowTitle(self.tr("Unique ID Generator"))

        layout = QVBoxLayout()

        self.field_input = QLineEdit("BSM")
        self.prefix_input = QLineEdit("130129")
        self.length_input = QSpinBox()
        self.length_input.setRange(10, 30)
        self.length_input.setValue(18)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems([self.tr("Global Unique"), self.tr("Layer Unique")])

        layout.addWidget(QLabel(self.tr("Field name:")))
        layout.addWidget(self.field_input)
        layout.addWidget(QLabel(self.tr("Prefix:")))
        layout.addWidget(self.prefix_input)
        layout.addWidget(QLabel(self.tr("Total length:")))
        layout.addWidget(self.length_input)
        layout.addWidget(QLabel(self.tr("Uniqueness scope:")))
        layout.addWidget(self.scope_combo)

        layout.addWidget(QLabel(self.tr("Select layers:")))
        self.layer_list = QListWidget()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                item = QListWidgetItem(layer.name())
                item.setCheckState(0)
                self.layer_list.addItem(item)
        layout.addWidget(self.layer_list)

        run_btn = QPushButton(self.tr("Generate"))
        run_btn.clicked.connect(self.generate_ids)
        layout.addWidget(run_btn)

        self.dlg.setLayout(layout)
        self.dlg.exec_()

    def generate_ids(self):
        prefix = self.prefix_input.text().strip()
        total_length = self.length_input.value()
        field_name = self.field_input.text().strip()
        global_unique = self.scope_combo.currentIndex() == 0

        selected_layers = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item.checkState():
                name = item.text()
                layer = next((l for l in QgsProject.instance().mapLayers().values() if l.name() == name), None)
                if layer:
                    selected_layers.append(layer)

        if not selected_layers:
            QMessageBox.warning(None, self.tr("Warning"), self.tr("No layers selected."))
            return

        global_counter = 1
        for layer in selected_layers:
            if not layer.isEditable():
                layer.startEditing()
            if field_name not in [f.name() for f in layer.fields()]:
                layer.dataProvider().addAttributes([QgsField(field_name, QVariant.String)])
                layer.updateFields()
            features = list(layer.getFeatures())
            features.sort(key=lambda f: f.id())
            for idx, feat in enumerate(features, 1):
                seq = global_counter if global_unique else idx
                code = f"{prefix}{str(seq).zfill(total_length - len(prefix))}"
                layer.changeAttributeValue(feat.id(), layer.fields().indexOf(field_name), code)
                if global_unique:
                    global_counter += 1
            layer.commitChanges()

        QMessageBox.information(None, self.tr("Done"), self.tr("Unique IDs have been assigned."))

    def tr(self, text):
        return QCoreApplication.translate("UniqueIDGenerator", text)
