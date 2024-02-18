from odoo import _, api, fields, models, tools
from datetime import datetime
from odoo.exceptions import UserError
import random


class SecurityEmployeeExitEntry(models.Model):
    _name = "osoul.security.emp.exit.enter"
    _description = "Security Employee Exit and Entry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "emp_id_no"

    record_no = fields.Char(string="Record No", tracking=True)
    emp_name_id = fields.Many2one(
        string="Employee Name",
        comodel_name="hr.employee",
        ondelete="restrict",
        required=True,
        domain = ['|',('in_out_status', '=', 'draft'), ('in_out_status', '=', 'inside_osoul')],
        tracking=True,
    )
    emp_id_no = fields.Char(
        related="emp_name_id.employment_no", string="Employee ID", tracking=True
    )
    emp_department_id = fields.Many2one(
        related="emp_name_id.department_id",
        string="Department",
        readonly=True,
        store=True,
        tracking=True,
    )
    emp_phone = fields.Char(
        related="emp_name_id.mobile_phone", string="Phone No", tracking=True
    )
    in_out_status = fields.Selection(
        related="emp_name_id.in_out_status",
        string="Status",
        readonly=True,
        tracking=True,
    )
    time_out = fields.Datetime(
        string="Exiting Time", readonly=True, tracking=True)
    exit_gate_id = fields.Many2one(
        string="Exiting Gate",
        comodel_name="osoul.security.poultry.gates",
        ondelete="restrict",
        tracking=True,
    )
    guard_in_exiting_id = fields.Many2one(
        string="Exiting Guard",
        comodel_name="res.users",
        ondelete="restrict",
        tracking=True,
    )
    time_in = fields.Datetime(string="Entering Time",
                              readonly=True, tracking=True)
    entry_gate_id = fields.Many2one(
        string="Entering Gate",
        comodel_name="osoul.security.poultry.gates",
        ondelete="restrict",
        tracking=True,
    )
    guard_in_entry_id = fields.Many2one(
        string="Entering Guard",
        comodel_name="res.users",
        ondelete="restrict",
        tracking=True,
    )
    time_spent_outsidee = fields.Char(
        string="Time Spent Outside",
        compute="_compute_time_spent_outside",
        store=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("outside_osoul", "Outside Osoul"),
            ("inside_osoul", "Inside Osoul"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

   
    exit_type = fields.Selection(
        [
            ("normal_exit", "Normal Exit"),
            ("vacation", "Vacation"),
            ("final_exit", "Final Exit"),
        ],
        string="Exit Type",
        default="normal_exit",
        tracking=True,
    )
    progress = fields.Integer(string="Progress", compute="_compute_progress")


    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            if rec.state == "draft":
                progress = random.randrange(4, 25)
            elif rec.state == "outside_osoul":
                progress = random.randrange(50, 85)
            elif rec.state == "inside_osoul":
                progress = 100
            else :
                progress = 0 
            rec.progress = progress


    @api.depends("time_in", "time_out")
    def _compute_time_spent_outside(self):
        for record in self:
            if record.time_in and record.time_out:
                time_out = record.time_out
                time_in = record.time_in
                time_spent = time_in - time_out
                hours = time_spent.seconds // 3600
                minutes = (time_spent.seconds // 60) % 60
                seconds = time_spent.seconds % 60
                record.time_spent_outsidee = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                record.time_spent_outsidee = "00:00:00"

    def action_button_outside_osoul(self):
        self.state = "outside_osoul"
        self.time_out = datetime.now()
        self.emp_name_id.in_out_status = "outside_osoul"
        self.guard_in_exiting_id = self.env.user.id
        self.record_no = self.env["ir.sequence"].next_by_code(
            "security_emp_exit_enter_sequence"
        )

    def action_button_inside_osoul(self):
        self.state = "inside_osoul"
        self.time_in = datetime.now()
        self.emp_name_id.in_out_status = "inside_osoul"
        self.guard_in_entry_id = self.env.user.id

        

    @api.model
    def _check_deletion_restrictions(self):
        restricted_states = ['inside_osoul', 'outside_osoul']
        restrict_records = self.filtered(
            lambda r: r.state in restricted_states)
        if restrict_records:
            raise UserError(
                _("Deletion of records is not allowed when the state is 'inside_osoul' or 'outside_osoul'."))

    def unlink(self):
        self._check_deletion_restrictions()
        return super(SecurityEmployeeExitEntry, self).unlink()