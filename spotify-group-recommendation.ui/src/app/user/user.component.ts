import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-user',
  templateUrl: './user.component.html',
  styleUrls: ['./user.component.css']
})
export class UserComponent implements OnInit {
  constructor(private router: Router, private activatedRoute: ActivatedRoute) {}

  public ngOnInit() {
  }

  public onClickPlaylists() {
    this.router.navigate(['playlists'], {relativeTo: this.activatedRoute})
  }

  public onClickGroups() {
    this.router.navigate(['groups'], {relativeTo: this.activatedRoute})
  }

  public onClickDetails() {
    this.router.navigate(['details'], {relativeTo: this.activatedRoute})
  }
}
