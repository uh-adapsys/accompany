#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QInputDialog>
#include <QDebug>
#include <QMessageBox>


QSqlDatabase db;
bool dbOpen;
int experimentLocation;


MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    closeDownRequest = false;
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::setup()
{

    bool ok;
    QString host, user, pw, dBase;

    QFile file("../UHCore/Core/config/database.yaml");

    if (!file.exists())
    {
       qDebug()<<"No database config found!!";
    }

    if (!file.open(QIODevice::ReadOnly | QIODevice::Text))
    {
        closeDownRequest = true;
        return;
    }

    QTextStream in(&file);
    while (!in.atEnd())
    {
       QString line = in.readLine();

       if (line.startsWith("mysql_log_user"))
       {
          user = line.section(":",1,1);
       }
       if (line.startsWith("mysql_log_password"))
       {
           pw = line.section(":",1,1);
       }
       if (line.startsWith("mysql_log_server"))
       {
          host = line.section(":",1,1);
       }
       if (line.startsWith("mysql_log_db"))
       {
          dBase = line.section(":",1,1);
       }
    }

    user = QInputDialog::getText ( this, "Accompany DB", "User:",QLineEdit::Normal,
                                     user, &ok);
    if (!ok)
    {
       closeDownRequest = true;
       return;
    }

    pw = QInputDialog::getText ( this, "Accompany DB", "Password:", QLineEdit::Password,
                                                                      pw, &ok);
    if (!ok)
    {
       closeDownRequest = true;
       return;
    }


    host = QInputDialog::getText ( this, "Accompany DB", "Host:",QLineEdit::Normal,
                                     host, &ok);
    if (!ok)
    {
      closeDownRequest = true;
      return;
    };

    dBase = QInputDialog::getText ( this, "Accompany DB", "Database:",QLineEdit::Normal,
                                     dBase, &ok);
    if (!ok)
    {
      closeDownRequest = true;
      return;
    };







    db = QSqlDatabase::addDatabase("QMYSQL");

    db.setHostName(host);
    db.setDatabaseName(dBase);
    db.setUserName(user);
    db.setPassword(pw);

    dbOpen = db.open();

    if (!dbOpen)
    {

        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Critical);

        msgBox.setText("Database error - login problem - see console log!");
        msgBox.exec();

        qCritical("Cannot open database: %s (%s)",
                  db.lastError().text().toLatin1().data(),
                  qt_error_string().toLocal8Bit().data());

        closeDownRequest = true;

        return;
    }
    else
    {
        qDebug() << "Database Opened";
    }

    // get experimental location


    QSqlQuery query("SELECT ExperimentalLocationId  FROM SessionControl WHERE SessionId = 1 LIMIT 1");

    if (query.next())
    {
       experimentLocation = query.value(0).toInt();
    }
    else
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Critical);

        msgBox.setText("Can find session control table!");
        msgBox.exec();
        closeDownRequest = true;
        return;
    }

     ui->locnlabel->setText(user + ":" + host + ":" + dBase);


     ui->changePushButton->setEnabled(false);
     ui->delPushButton->setEnabled(false);
     ui->pushButton->setEnabled(false);


    fillSensorComboBox();
    clearForm();

}


void MainWindow::setRuleCombo()
{
    ui->ruleComboBox->addItem("Boolean");
    ui->ruleComboBox->addItem("Moving Average");
    ui->ruleComboBox->addItem("Predicate");
    ui->ruleComboBox->addItem("N/A");
    ui->ruleComboBox->addItem("Watts >");
}

void MainWindow::fillSensorComboBox()
{
    QString seqQuery;
    QSqlQuery query;



    seqQuery = "SELECT sensorId,name FROM Sensors order by sensorId";

    query = seqQuery;

    ui->sensorComboBox->clear();

    ui->sensorComboBox->addItem("New Sensor");

    query.exec();

    while(query.next())
    {
        ui->sensorComboBox->addItem("::" + query.value(0).toString() + ":: " + query.value(1).toString());
    }

    ui->sensorComboBox->clearEditText();

}


void MainWindow::fillRuleComboBox(QString rule)
{


    int idx =0 ;

    if (rule == "Boolean") idx = 0;
    if (rule == "Moving Average") idx = 1;
    if (rule == "Predicate") idx = 2;
    if (rule == "N/A") idx = 3;
    if (rule.contains("Watts >"))
    {
        ui->ruleComboBox->setItemText(4,rule);
        idx=4;
    }
    ui->ruleComboBox->setCurrentIndex(idx);
}


void MainWindow::clearForm()
{
    fillSensorComboBox();

    ui->idSpinBox->setValue(0);

    ui->namePlainTextEdit->setPlainText("");
    ui->valuePlainTextEdit->setPlainText("");
    ui->prevValuePlainTextEdit->setPlainText("");
    ui->prevStatusPlainTextEdit->setPlainText("");
    ui->statusPlainTextEdit->setPlainText("");

    QDateTime t;
    t.setDate(QDate(2000,1,1));
    t.setTime(QTime(0,0));
    ui->locnComboBox->clear();
    ui->accessPointComboBox->clear();

    ui->currentDateTimeEdit->setDateTime(t);
    ui->prevDateTimeEdit->setDateTime(t);

    ui->ruleComboBox->clear();
    ui->channelPlainTextEdit->setPlainText("");

    ui->sensorTypeComboBox->clear();
    ui->xSpinBox->setValue(0);
    ui->ySpinBox->setValue(0);
    ui->oSpinBox->setValue(0);
    ui->ispinBox->setValue(0);

    fillLocationComboBox(0);
    fillAccessPointComboBox(5);
    setRuleCombo();
    fillRuleComboBox("N/A");
    fillSensorTypeComboBox(0);
}


void MainWindow::on_sensorComboBox_activated(const QString &arg1)
{
    ui->changePushButton->setEnabled(true);
    ui->delPushButton->setEnabled(true);
    ui->pushButton->setEnabled(true);

    if (arg1 == "New Sensor")
    {
        ui->addPushButton->setEnabled(true);
        ui->changePushButton->setEnabled(false);
        ui->delPushButton->setEnabled(false);
        ui->pushButton->setEnabled(false);
        ui->idSpinBox->setEnabled(true);
        clearForm();
        return;
    }

    ui->addPushButton->setEnabled(false);

    QString sensorId = arg1.section("::",1,1);

    QString seqQuery;
    QSqlQuery query;

    seqQuery = "SELECT * FROM Sensors where sensorId = " + sensorId;

    query = seqQuery;

    query.exec();

    while(query.next())
    {
        ui->idSpinBox->setValue(query.value(0).toInt());

        ui->idSpinBox->setEnabled(false);

        ui->namePlainTextEdit->setPlainText(query.value(3).toString());
        fillLocationComboBox(query.value(2).toInt());
        fillAccessPointComboBox(query.value(4).toInt());

        ui->valuePlainTextEdit->setPlainText(query.value(1).toString());
        ui->statusPlainTextEdit->setPlainText(query.value(11).toString());
        ui->currentDateTimeEdit->setDateTime(query.value(8).toDateTime());

        ui->prevValuePlainTextEdit->setPlainText(query.value(10).toString());
        ui->prevStatusPlainTextEdit->setPlainText(query.value(12).toString());
        ui->prevDateTimeEdit->setDateTime(query.value(9).toDateTime());

        setRuleCombo();
        fillRuleComboBox(query.value(5).toString());

        ui->channelPlainTextEdit->setPlainText(query.value(6).toString());

        fillSensorTypeComboBox(query.value(7).toInt());

        ui->xSpinBox->setValue(query.value(13).toFloat());
        ui->ySpinBox->setValue(query.value(14).toFloat());
        ui->oSpinBox->setValue(query.value(15).toFloat());
        ui->ispinBox->setValue(query.value(16).toInt());

    }


}

void MainWindow::on_sensorComboBox_editTextChanged(const QString &arg1)
{
 //   ui->changePushButton->setEnabled(false);
 //   ui->delPushButton->setEnabled(false);

}



void MainWindow::fillLocationComboBox(int locnId)
{
    int idx = 0;
    int selectedIdx = 0;
    QString locQuery;

    locQuery = "SELECT  L1.locationId, L1.where, L2.where, L1.name, IF(STRCMP(L1.name,L2.name),L2.name,''), IF(STRCMP(L2.name,L3.name),L3.name,''), IF(STRCMP(L3.name,L4.name),L4.name,'')\
           FROM Locations L1,\
                Locations L2,\
                Locations L3,\
                Locations L4\
           WHERE L2.locationId = L1.where\
             AND L3.locationId = L2.where\
             AND L4.locationId = L3.where";

    if (experimentLocation == 1)
    {
       locQuery += " AND (L1.locationId < 300 OR L1.locationId = 999) ORDER BY L1.locationId";
    }

    if (experimentLocation == 2)
    {
        locQuery += " AND ((L1.locationId > 599 AND L1.locationId < 700) or L1.locationId = 999) ORDER BY L1.locationId";
    }

    if (experimentLocation == 3)
    {
        locQuery += " AND ((L1.locationId > 699 AND L1.locationId < 800) or L1.locationId = 999) ORDER BY L1.locationId";
    }

    if (experimentLocation == 6)
    {
        locQuery += " AND ((L1.locationId > 299 AND L1.locationId < 400) or L1.locationId = 999) ORDER BY L1.locationId";
    }

//   qDebug() << locQuery;

    QSqlQuery query(locQuery);

    ui->locnComboBox->clear();

    QString q1, q2, q3;

    q1 = q2 = q3 = "";

    while(query.next())
    {
        q1 = q2 = q3 = "";

        if ( query.value(4).toString() != "")
        {
            if ( query.value(1) == 0)
            {
                q1 = "";
            }
            else
            {
                q1 = " in the " +   query.value(4).toString();
            }
        }

        if ( query.value(5).toString() != "")
        {
            if ( query.value(2) == 0)
            {
                q2 = "";
            }
            else
            {
                q2 = " of the " +   query.value(5).toString();
            }
        }



        if (query.value(0).toInt() == locnId)
        {
            selectedIdx = idx;
        }

        ui->locnComboBox->addItem( "::" + query.value(0).toString() + ":: " + query.value(3).toString() + q1 + q2 );

        idx++;

    }

    ui->locnComboBox->setCurrentIndex(selectedIdx);

}

void MainWindow::fillAccessPointComboBox(int accessPoint)
{
    int idx = 0;
    int selectedIdx = 0;
    QString accQuery;


    accQuery = "SELECT * FROM SensorAccessPoint";

    QSqlQuery query(accQuery);

    ui->accessPointComboBox->clear();



    while(query.next())
    {


        if (query.value(0).toInt() == accessPoint)
        {
            selectedIdx = idx;
        }

        ui->accessPointComboBox->addItem( "::" + query.value(0).toString() + ":: " + query.value(2).toString());

        idx++;

    }

    ui->accessPointComboBox->setCurrentIndex(selectedIdx);

}

void MainWindow::fillSensorTypeComboBox(int sensorType)
{
    int idx = 0;
    int selectedIdx = 0;
    QString accQuery;


    accQuery = "SELECT * FROM SensorType";

    QSqlQuery query(accQuery);

    ui->sensorTypeComboBox->clear();

    while(query.next())
    {

        if (query.value(0).toInt() == sensorType)
        {
            selectedIdx = idx;
        }

        ui->sensorTypeComboBox->addItem( "::" + query.value(0).toString() + ":: " + query.value(1).toString());

        idx++;

    }

    ui->sensorTypeComboBox->setCurrentIndex(selectedIdx);

}


void MainWindow::on_changePushButton_clicked()
{
    if (ui->sensorComboBox->currentText() == "")
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a sensor to change!");
        msgBox.exec();

        return;
    }

    if (!updateSensor()) return;

    clearForm();

}

bool MainWindow::updateSensor()
{
    QSqlQuery query;
    query.prepare("UPDATE Sensors SET \
                value = :value,\
                locationId = :locationId,\
                name = :name,\
                sensorAccessPointID = :sensorAccessPointID,\
                sensorRule = :sensorRule,\
                ChannelDescriptor = :ChannelDescriptor,\
                sensorTypeId = :sensorTypeId,\
                lastUpdate = :lastUpdate,\
                lastTimeActive = :lastTimeActive,\
                lastActiveValue = :lastActiveValue,\
                status = :status,\
                lastStatus = :lastStatus,\
                xCoord = :xCoord,\
                yCoord = :yCoord,\
                orientation = :orientation,\
                icon = :icon\
                WHERE sensorId = :id");

    query.bindValue(":id",ui->sensorComboBox->currentText().section("::",1,1));
    query.bindValue(":locationId",ui->locnComboBox->currentText().section("::",1,1));
    query.bindValue(":value",ui->valuePlainTextEdit->toPlainText().trimmed());
    query.bindValue(":lastActiveValue",ui->prevValuePlainTextEdit->toPlainText().trimmed());
    query.bindValue(":name",ui->namePlainTextEdit->toPlainText().trimmed());
    query.bindValue(":sensorAccessPointID",ui->accessPointComboBox->currentText().section("::",1,1));
    query.bindValue(":sensorRule",ui->ruleComboBox->currentText());
    query.bindValue(":ChannelDescriptor",ui->channelPlainTextEdit->toPlainText().trimmed());
    query.bindValue(":sensorTypeId",ui->sensorTypeComboBox->currentText().section("::",1,1));
    query.bindValue(":lastUpdate",ui->currentDateTimeEdit->dateTime().toString(Qt::ISODate));
    query.bindValue(":lastTimeActive",ui->prevDateTimeEdit->dateTime().toString(Qt::ISODate));
    query.bindValue(":status",ui->statusPlainTextEdit->toPlainText().trimmed());
    query.bindValue(":lastStatus",ui->prevStatusPlainTextEdit->toPlainText().trimmed());
    query.bindValue(":xCoord",ui->xSpinBox->value());
    query.bindValue(":yCoord",ui->ySpinBox->value());
    query.bindValue(":orientation",ui->oSpinBox->value());
    query.bindValue(":icon",ui->ispinBox->value());

    if (!query.exec())
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Critical);

        msgBox.setText("Database error - can't update Sensors table!");
        msgBox.exec();

        qCritical("Cannot update: %s (%s)",
              db.lastError().text().toLatin1().data(),
              qt_error_string().toLocal8Bit().data());
        return false;
    }
}



void MainWindow::on_delPushButton_clicked()
{
    if (ui->sensorComboBox->currentText() == "")
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a sensor to delete!");
        msgBox.exec();

        return;
    }


    int ret = QMessageBox::warning(this, tr("Sensor Maintenance"),
                                   tr("Do you really want to delete this sensor?"),
                                   QMessageBox::Cancel | QMessageBox::Yes);

    if (ret == QMessageBox::Cancel)
    {
        return;
    }


    QSqlQuery query;
    query.prepare("DELETE FROM Sensors WHERE sensorid = :id");
    query.bindValue(":id",ui->sensorComboBox->currentText().section("::",1,1));

    if (!query.exec())
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Critical);

        msgBox.setText("Database error - can't delete from Sensors table!");
        msgBox.exec();

        qCritical("Cannot delete: %s (%s)",
                  db.lastError().text().toLatin1().data(),
                  qt_error_string().toLocal8Bit().data());
        return;

    }


 //   fillSensorComboBox();
    clearForm();

}


void MainWindow::on_pushButton_clicked()   // switch
{
    QString current;
    current = ui->valuePlainTextEdit->toPlainText().trimmed();
    ui->valuePlainTextEdit->setPlainText(ui->prevValuePlainTextEdit->toPlainText().trimmed());
    ui->prevValuePlainTextEdit->setPlainText(current);

    current = ui->statusPlainTextEdit->toPlainText().trimmed();
    ui->statusPlainTextEdit->setPlainText(ui->prevStatusPlainTextEdit->toPlainText().trimmed());
    ui->prevStatusPlainTextEdit->setPlainText(current);


    ui->prevDateTimeEdit->setDateTime(ui->currentDateTimeEdit->dateTime());

    QSqlQuery query;
    query.clear();
    query.exec("select fnGetSchedulerDateTime()");

    while (query.next())
    {
        ui->currentDateTimeEdit->setDateTime(query.value(0).toDateTime());
    }

    updateSensor();
}

void MainWindow::on_addPushButton_clicked()
{
    ui->idSpinBox->setEnabled(true);

    if (ui->idSpinBox->value() == 0)
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a sensor number!");
        msgBox.exec();

        return;
    }

    QString seqQuery;
    QSqlQuery query;

    QString vl;
    vl.setNum(ui->idSpinBox->value());
    seqQuery = "SELECT * FROM Sensors where sensorId = " + vl;

    query = seqQuery;

    query.exec();

    while(query.next())
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("A sensor with that number already exists!");
        msgBox.exec();

        return;
    }


    if (ui->namePlainTextEdit->toPlainText().trimmed() == "")
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a sensor name!");
        msgBox.exec();

        return;
    }

    if (ui->valuePlainTextEdit->toPlainText().trimmed() == "")
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a value!");
        msgBox.exec();

        return;
    }

    if (ui->prevValuePlainTextEdit->toPlainText().trimmed() == "")
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a previous value!");
        msgBox.exec();

        return;
    }

    if (ui->channelPlainTextEdit->toPlainText().trimmed() == "")
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a channel descriptor!");
        msgBox.exec();

        return;
    }

    if (ui->statusPlainTextEdit->toPlainText().trimmed() == "")
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a current status!");
        msgBox.exec();

        return;
    }

    if (ui->prevStatusPlainTextEdit->toPlainText().trimmed() == "")
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Warning);

        msgBox.setText("You need to provide a previous status!");
        msgBox.exec();

        return;
    }


    query.clear();
    query.prepare("INSERT INTO Sensors VALUES (:sensorId,:value,:locationId,:name,:sensorAccessPointID,:sensorRule,:ChannelDescriptor,:sensorTypeId,:lastUpdate,:lastTimeActive,:lastActiveValue,:status,:lastStatus,:xCoord,:yCoord,:orientation,:icon)");
    QString id;
    id.setNum(ui->idSpinBox->value());
    query.bindValue(":sensorId",id);
    query.bindValue(":locationId",ui->locnComboBox->currentText().section("::",1,1));
    query.bindValue(":value",ui->valuePlainTextEdit->toPlainText().trimmed());
    query.bindValue(":lastActiveValue",ui->prevValuePlainTextEdit->toPlainText().trimmed());
    query.bindValue(":name",ui->namePlainTextEdit->toPlainText().trimmed());
    query.bindValue(":sensorAccessPointID",ui->accessPointComboBox->currentText().section("::",1,1));
    query.bindValue(":sensorRule",ui->ruleComboBox->currentText());
    query.bindValue(":ChannelDescriptor",ui->channelPlainTextEdit->toPlainText().trimmed());
    query.bindValue(":sensorTypeId",ui->sensorTypeComboBox->currentText().section("::",1,1));
    query.bindValue(":lastUpdate",ui->currentDateTimeEdit->dateTime().toString(Qt::ISODate));
    query.bindValue(":lastTimeActive",ui->prevDateTimeEdit->dateTime().toString(Qt::ISODate));
    query.bindValue(":status",ui->statusPlainTextEdit->toPlainText().trimmed());
    query.bindValue(":lastStatus",ui->prevStatusPlainTextEdit->toPlainText().trimmed());
    query.bindValue(":xCoord",ui->xSpinBox->value());
    query.bindValue(":yCoord",ui->ySpinBox->value());
    query.bindValue(":orientation",ui->oSpinBox->value());
    query.bindValue(":icon",ui->ispinBox->value());

    if (!query.exec())
    {
        QMessageBox msgBox;
        msgBox.setIcon(QMessageBox::Critical);

        msgBox.setText("Database error - can't insert to Sensors table!");
        msgBox.exec();

        qCritical("Cannot add: %s (%s)",
              db.lastError().text().toLatin1().data(),
              qt_error_string().toLocal8Bit().data());
        return;
    }

    clearForm();
}
